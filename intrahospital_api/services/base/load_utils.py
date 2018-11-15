from functools import wraps
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from opal.models import Patient
from intrahospital_api import logger
from intrahospital_api.exceptions import BatchLoadError
from intrahospital_api import models

MAX_ALLOWABLE_BATCH_RUN_TIME = 3600


def any_loads_running():
    """
    Returns a boolean as to whether any loads are
    running, for use by things that synch databases
    """
    patient_loading = models.InitialPatientLoad.objects.filter(
        state=models.InitialPatientLoad.RUNNING
    ).exists()

    batch_loading = models.BatchPatientLoad.objects.filter(
        state=models.BatchPatientLoad.RUNNING
    ).exists()
    result = patient_loading or batch_loading
    logger.info("Checking loads are running {}".format(result))
    return result


def good_to_go(service_name):
    """
    Are we good to run a batch load, returns True if we should.
    runs a lot of sanity checks.
    """
    batch_loads = models.BatchPatientLoad.objects.filter(
        service_name=service_name
    )

    if not batch_loads.exists():
        return True

    last_run_running = batch_loads.filter(
        Q(stopped=None) | Q(state=models.BatchPatientLoad.RUNNING)
    ).first()

    # If the previous load is still running we don't want to start a new one.
    if last_run_running:
        time_ago = timezone.now() - last_run_running.started

        if time_ago.seconds < MAX_ALLOWABLE_BATCH_RUN_TIME:
            logger.info(
                "batch still running after {} seconds".format(
                    time_ago.seconds
                )
            )
            return False
        else:
            # The batch has been running for too long. Email us to look at it
            logger.error(
                "Previous batch load for {} still running after {} seconds".format(
                    service_name, MAX_ALLOWABLE_BATCH_RUN_TIME
                )
            )
            return False

    return True


def get_batch_start_time(service_name):
    """
    If no previous successful batch run has started.
    Use the started timestamp of the first Initial Patient Load

    If a previous batch load has run and there was an initial patient
    load that finished within that time and started before it
    use the start time of the inital patient load.

    In most cases we should be using the start time of the previous
    BatchPatientLoad

    ie batch A starts at 10:00 and finishes at 10:03
    batch B will get all data since 10:00 so that nothing is lost

    however...
    the batches exclude initial patient loads, but usually that's ok
    but we have extra cracks to paper over...

    a patient load starts during the batch A load, at 9:58. It finishes
    the db load from the upstream db at 9:59 but is still saving the data
    to our db at 10:00

    it is excluded from the batch A, so batch B goes and starts its run
    from 9:59 accordingly.

    e.g.
        1. Batch A starts.
        2. Patient Y is added, their personal load is started.
        3. Batch A finishes.
        4. Batch B starts
        5. Patient Y's load finishes.
        6. Batch B stops

        7. Batch C starts.

        What time should Batch C load from?
        It starts from the time at 2
    """
    last_successful_run = models.BatchPatientLoad.objects.filter(
        state=models.BatchPatientLoad.SUCCESS,
        service_name=service_name
    ).order_by("started").last()

    if not last_successful_run:
        return models.InitialPatientLoad.objects.order_by("started").first().started

    long_patient_load = models.InitialPatientLoad.objects.filter(
        state=models.InitialPatientLoad.SUCCESS
    ).filter(
        started__lt=last_successful_run.started
    ).filter(
        stopped__gt=last_successful_run.started
    ).order_by("started").first()

    if long_patient_load:
        return long_patient_load.started
    else:
        return last_successful_run.started


def batch_load(service_name):
    """
    A decorator that runs the function as batch load
    ie wrapping it in the batch load decorator

    A Batch load is wrapped in a model called
    the BatchPatientLoad records when it starts and stops.

    The function we calling is expected to return
    a integer which should be a count of the objects
    (be they lab tests, appointments, demographics etc)
    that have changed.

    The wrapper also handles if an error is thrown it
    notifies developers that a batch load error.
    """
    def batch_load_wrapper(fun):
        @wraps(fun)
        @transaction.atomic
        def wrap(*args, **kwargs):
            if not good_to_go(service_name):
                logger.info("batch {} not ready skipping".format(service_name))
                return
            logger.info("starting batch load for {}".format(service_name))
            batch = models.BatchPatientLoad(service_name=service_name)
            batch.start()
            try:
                count = fun(*args, **kwargs)
            except Exception as e:
                batch.failed()
                logger.error("{} batch load error {}".format(
                    service_name, str(e)
                ))
            else:
                batch.count = count
                batch.complete()

                if not isinstance(count, int):
                    raise ValueError("batch load should return an integer")
        return wrap
    return batch_load_wrapper


def get_loaded_patients():
    return Patient.objects.filter(initialpatientload__state=models.InitialPatientLoad.SUCCESS)



