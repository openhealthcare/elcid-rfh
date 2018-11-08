import logging
import time
from functools import wraps
from pytds.tds import OperationalError
from django.conf import settings
import pytds


logger = logging.getLogger('intrahospital_api')

# if we fail in a query, the amount of seconds we wait before retrying
RETRY_DELAY = 30


def db_retry(f):
    """ We are reading a database that is also receiving intermittent writes.
        When these writes are coming the DB locks.
        Lets put in a retry after 30 seconds
    """
    @wraps(f)
    def wrap(*args, **kw):
        try:
            result = f(*args, **kw)
        except OperationalError as o:
            logger.info('{}: failed with {}, retrying in {}s'.format(
                f.__name__, str(o), RETRY_DELAY
            ))
            time.sleep(RETRY_DELAY)
            result = f(*args, **kw)
        return result
    return wrap


def to_date_str(some_date):
    """ we return something that is 'updatedable by dict'
        so we need to convert all dates into strings
    """
    if some_date:
        return some_date.strftime(settings.DATE_INPUT_FORMATS[0])


def to_datetime_str(some_datetime):
    """ we return something that is 'updatedable by dict'
        so we need to convert all datetimes into strings
    """
    if some_datetime:
        return some_datetime.strftime(settings.DATETIME_INPUT_FORMATS[0])


class Row(object):
    """
    a simple wrapper to get us the fields we actually want out of a row

    example use:

    class DemographicsRow(Row):
        MAPPINGS = {
            "hospital_number": "patient_number",
            "name": "name",
            "date_of_birth": ("primary_field", "secondary_field",)
        }

        @property
        def name(self):
            return "{} {}".format(
                self.raw_data["first_name"], self.raw_data["last_name"]
            )

    raw_data = dict(
        patient_number="1",
        first_name="Wilma",
        last_name="Flintstone",
        secondary_field="1/1/2000"
    )
    demographics_row = DemographicsRow(raw_data)

    demographics_row.hospital_number == "1"
    demographics_row.name == "Wilma Flintstone"
    demographics_row.date_of_birth == "1/1/2000"
    """
    FIELD_MAPPINGS = {}

    def __init__(self, raw_data):
        self.raw_data = raw_data

    def _get_or_fallback(self, primary_field, secondary_field):
        """ look at one field, if its empty, use a different field
        """
        # if we have a source that is not always possible
        # this checks for one field being populated and
        # falls back to another if its not populated
        result = self.raw_data.get(primary_field)

        if not result:
            result = self.raw_data.get(secondary_field, "")

        return result

    def __getattr__(self, key):
        translated_field = self.FIELD_MAPPINGS[key]

        if isinstance(translated_field, (tuple, list)):
            return self._get_or_fallback(
                translated_field[0], translated_field[1]
            )

        # used by properties
        if hasattr(self, translated_field):
            return getattr(self, translated_field)

        return self.raw_data[translated_field]


class DBConnection(object):
    def __init__(self):
        self.ip_address = settings.HOSPITAL_DB["IP_ADDRESS"]
        self.database = settings.HOSPITAL_DB["DATABASE"]
        self.username = settings.HOSPITAL_DB["USERNAME"]
        self.password = settings.HOSPITAL_DB["PASSWORD"]

    @db_retry
    def execute_query(self, query, **params):
        with pytds.connect(
            self.ip_address,
            self.database,
            self.username,
            self.password,
            as_dict=True
        ) as conn:
            with conn.cursor() as cur:
                logger.info(
                    "Running upstream query {} {}".format(query, params)
                )
                cur.execute(query, params)
                result = cur.fetchall()
        logger.info(result)
        return result

    @db_retry
    def execute_query_multiple_times(self, query, list_of_params):
        """
        Iterates over a list of params and executes
        the same query each time for each param
        """
        result = []
        with pytds.connect(
            self.ip_address,
            self.database,
            self.username,
            self.password,
            as_dict=True
        ) as conn:
            for params in list_of_params:
                with conn.cursor() as cur:
                    logger.info(
                        "Running upstream query {} {}".format(query, params)
                    )
                    cur.execute(query, params)
                    result.extend(cur.fetchall())
        logger.info(result)
        return result
