from django.utils import timezone
from intrahospital_api import loader
from opal.core import subrecords
from django.db import transaction
from elcid import models as elcid_models
from plugins.admissions import models as admission_models
from plugins.appointments import models as appointment_models
from plugins.covid import models as covid_models
from plugins.dischargesummary import models as discharge_models
from plugins.handover import models as handover_models
from plugins.ipc import models as ipc_models
from plugins.imaging import models as imaging_models
from intrahospital_api import models as intrahospital_api_models
from plugins.icu import models as icu_models
from plugins.rnoh import models as rnoh_models
from plugins.tb import models as tb_models
from obs import models as obs_models
from opal import models as opal_models
import reversion


IGNORED_FIELDS = {"id", "episode", "patient", "previous_mrn"}

# All models with a foriegn key to Patient that should be moved over
PATIENT_RELATED_MODELS = [
    admission_models.BedStatus,
    admission_models.TransferHistory,
    admission_models.UpstreamLocation,
    covid_models.CovidVaccination,
    covid_models.CovidPatient,
    discharge_models.DischargeSummary,
    elcid_models.BloodCultureSet,
    elcid_models.ChronicAntifungal,
    elcid_models.GP,
    elcid_models.PositiveBloodCultureHistory,
    elcid_models.RiskFactor,
    handover_models.AMTHandover,
    handover_models.NursingHandover,
    icu_models.ICUHandover,
    icu_models.ICUHandoverLocation,
    icu_models.ICUHandoverLocationHistory,
    intrahospital_api_models.ExternalDemographics,
    intrahospital_api_models.InitialPatientLoad,
    ipc_models.IPCStatus,
    opal_models.InpatientAdmission,
    opal_models.PatientRecordAccess,
    rnoh_models.RNOHDemographics,
    rnoh_models.RNOHTeams,
    tb_models.AFBCulture,
    tb_models.AFBRefLab,
    tb_models.AFBSmear,
    tb_models.AccessConsiderations,
    tb_models.Allergies,
    tb_models.BCG,
    tb_models.CommuninicationConsiderations,
    tb_models.ContactDetails,
    tb_models.Employment,
    tb_models.IndexCase,
    tb_models.MantouxTest,
    tb_models.Nationality,
    tb_models.NextOfKin,
    tb_models.Pregnancy,
    tb_models.TBHistory,
    tb_models.TBPCR,
]


# All models with a foriegn key to Episode that should be moved over
EPISODE_RELATED_MODELS = [
    elcid_models.Antimicrobial,
    elcid_models.Diagnosis,
    elcid_models.ICURound,
    elcid_models.Imaging,
    elcid_models.Infection,
    elcid_models.InfectionServiceNote,
    elcid_models.Line,
    elcid_models.Location,
    elcid_models.MicrobiologyInput,
    elcid_models.PastMedicalHistory,
    elcid_models.PrimaryDiagnosis,
    elcid_models.Procedure,
    elcid_models.ReferralRoute,
    elcid_models.SymptomComplex,
    obs_models.Observation,
    covid_models.CovidAdmission,
    covid_models.CovidComorbidities,
    covid_models.CovidFollowUpCall,
    covid_models.CovidFollowUpCallFollowUpCall,
    covid_models.CovidSixMonthFollowUp,
    covid_models.LungFunctionTest,
    ipc_models.InfectionAlert,
    rnoh_models.OPATEpisodes,
    rnoh_models.RNOHActions,
    rnoh_models.RNOHMicrobiology,
    tb_models.AdverseReaction,
    tb_models.LymphNodeSwellingSite,
    tb_models.OtherInvestigation,
    tb_models.PatientConsultation,
    tb_models.SocialHistory,
    tb_models.TBLocation,
    tb_models.TBManagement,
    tb_models.TBMeta,
    tb_models.Travel,
    tb_models.Treatment,
]

# Statuses that hold information in a field about the existence of
# another model. We do this for statuses that are not
# loaded in by _load_patient
STATUS_MODELS_TO_RELATED_MODEL = {
    discharge_models.PatientDischargeSummaryStatus: (
        "has_dischargesummaries",
        discharge_models.DischargeSummary,
    ),
    handover_models.PatientAMTHandoverStatus: (
        "has_handover",
        handover_models.AMTHandover,
    ),
    handover_models.PatientNursingHandoverStatus: (
        "has_handover",
        handover_models.NursingHandover,
    ),
}


def move_tagging(old_episode, new_episode):
    """
    Moves the tagging from the old episode to the new episode.

    We have no updated timestamp so consider the unarchived tag to be
    more important than the unarchived tag.

    If the old episode has an archived tag which is not
    on the new episdoe we move this over.
    """
    for old_tag in old_episode.tagging_set.all():
        new_tag = new_episode.tagging_set.filter(value=old_tag.value).first()
        if new_tag:
            if new_tag.archived and not old_tag.archived:
                # if tag on the old episode is not archived consider
                # then unarchive it then unarchive it on the new one
                new_tag.archived = False
                new_tag.user = old_tag.user
                new_tag.save()
        else:
            old_tag.episode_id = new_episode.id
            old_tag.id = None
            old_tag.save()


def update_singleton(subrecord_cls, old_parent, new_parent, old_mrn):
    """
    If the new singleton has never been edited, delete it
    and replace it with the old singleton keeping the revision history
    and updating the previous MRN. It creates a new revision entry for
    this change.

    If they have both been updated, but the new singleton is more
    recent do nothing.

    If they have both been updated, but the old singleton is more recent
    copy over the fields from the old singleton onto the new singleton and
    updagte the previous MRN on the subrecord. It creates a new revision entry for
    this change.
    """
    if new_parent.__class__ == opal_models.Episode:
        is_episode_subrecord = True
    else:
        is_episode_subrecord = False

    if is_episode_subrecord:
        old_singleton = subrecord_cls.objects.get(episode=old_parent)
        new_singleton = subrecord_cls.objects.get(episode=new_parent)
    else:
        old_singleton = subrecord_cls.objects.get(patient=old_parent)
        new_singleton = subrecord_cls.objects.get(patient=new_parent)
    if not old_singleton.updated:
        # the old singleton was never editted, we can skip
        return
    if not new_singleton.updated:
        # the new singleton was never editted, we can delete
        # it and replace it with the old one.
        new_singleton.delete()
        if is_episode_subrecord:
            old_singleton.episode = new_parent
        else:
            old_singleton.patient = new_parent
        old_singleton.previous_mrn = old_mrn
        with reversion.create_revision():
            old_singleton.save()
    else:
        if new_singleton.updated < old_singleton.updated:
            # the old singleton is new than the new singleton
            # stamp the new singleton as reversion
            # then copy over all the fields from the old
            # onto the new
            for field in old_singleton._meta.get_fields():
                field_name = field.name
                if field_name in IGNORED_FIELDS:
                    continue
                setattr(new_singleton, field_name, getattr(old_singleton, field_name))
            new_singleton.previous_mrn = old_mrn
            with reversion.create_revision():
                new_singleton.save()
        else:
            # the old singleton is older than the new singleton
            # create a reversion record with the data of the old
            # singleton, then continue with the more recent data
            more_recent_data = {}
            new_singleton.previous_mrn = old_mrn
            for field in new_singleton._meta.get_fields():
                field_name = field.name
                if field_name in IGNORED_FIELDS:
                    continue
                more_recent_data[field_name] = getattr(new_singleton, field_name)
                setattr(new_singleton, field_name, getattr(old_singleton, field_name))
            with reversion.create_revision():
                new_singleton.save()
            for field, value in more_recent_data.items():
                setattr(new_singleton, field, value)
            new_singleton.previous_mrn = None
            with reversion.create_revision():
                new_singleton.save()


def move_non_singletons(subrecord_cls, old_parent, new_parent, old_mrn):
    """
    Moves the old_subrecords query set onto the new parent (a patient or episode).
    In doing so it updates the previous_mrn field to be that of the old_mrn
    """
    if new_parent.__class__ == opal_models.Episode:
        is_episode_subrecord = True
    else:
        is_episode_subrecord = False

    if is_episode_subrecord:
        old_subrecords = subrecord_cls.objects.filter(episode=old_parent)
    else:
        old_subrecords = subrecord_cls.objects.filter(patient=old_parent)

    for old_subrecord in old_subrecords:
        if is_episode_subrecord:
            old_subrecord.episode = new_parent
        else:
            old_subrecord.patient = new_parent
        old_subrecord.previous_mrn = old_mrn
        with reversion.create_revision():
            old_subrecord.save()


def move_record(subrecord_cls, old_parent, new_parent, old_mrn):
    """
    Moves a subrecord_cl from an old parent (a patient or an episode)
    to a new one.
    """
    if getattr(subrecord_cls, "_is_singleton", False):
        update_singleton(subrecord_cls, old_parent, new_parent, old_mrn)
    else:
        move_non_singletons(subrecord_cls, old_parent, new_parent, old_mrn)


def updates_statuses(new_patient):
    """
    If the patient now has upstream models, make sure
    we update the corresponding status objects.
    """
    for status, related_field_and_model in STATUS_MODELS_TO_RELATED_MODEL.items():
        related_field, related_model = related_field_and_model
        exists = related_model.objects.filter(patient=new_patient).exists()
        status.objects.filter(patient=new_patient).update(**{related_field: exists})


@transaction.atomic
def merge_patient(*, old_patient, new_patient):
    """
    All elcid native non-singleton entries to be converted to
    the equivalent episode category on the wining MRN, with a reference
    created in the original_mrn field where they have been moved

    Copy teams from the old infection service episode? To the new
    Infection service episode

    Copy over any episode categories that do not exist, iterate
    over subrecord attached to these and add the PreviousMRN

    Singleton entries to pick the latest but create a reversion
    history entry for the non-oldest, with a reference to the original_mrn

    Non-singletons entries are moved from the old parent to the
    new parent.
    """
    old_mrn = old_patient.demographics().hospital_number
    for patient_related_model in PATIENT_RELATED_MODELS:
        move_record(
            patient_related_model,
            old_patient,
            new_patient,
            old_mrn,
        )
    for old_episode in old_patient.episode_set.all():
        # Note: if the old episode has multiple episode
        # categories of the same category name
        # this will merge those.
        new_episode, _ = new_patient.episode_set.get_or_create(
            category_name=old_episode.category_name
        )
        move_tagging(old_episode, new_episode)
        for episode_related_model in EPISODE_RELATED_MODELS:
            move_record(
                episode_related_model,
                old_episode,
                new_episode,
                old_mrn,
            )
    old_patient.delete()
    new_patient.mergedmrn_set.filter(mrn=old_mrn).update(
        our_merge_datetime=timezone.now()
    )
    updates_statuses(new_patient)
    loader.load_patient(new_patient, run_async=False)
