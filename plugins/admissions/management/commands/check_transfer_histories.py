"""
Management command that sends a sanity check
"""
import datetime
from django.conf import settings
from django.db.models import Max
from django.core.management import BaseCommand
from django.utils import timezone
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from plugins.admissions.models import TransferHistory
from django.core.mail import send_mail
import asyncio


def send_report(report):
    dt = datetime.datetime.now().strftime("%d/%m/%Y")
    report_str = "\n".join(report)
    send_mail(
        f"TransferHistory report {dt}",
        report_str,
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_CHECK_EMAIL],
    )


def last_updated():
    return TransferHistory.objects.aggregate(m=Max("updated_datetime"))["m"]


def upstream_count_all_time():
    api = ProdAPI()
    query = """
    SELECT COUNT(*) FROM INP.TRANSFER_HISTORY_EL_CID WITH (NOLOCK)
    WHERE LOCAL_PATIENT_IDENTIFIER is not null
    AND LOCAL_PATIENT_IDENTIFIER <> ''
    AND In_TransHist = 1
    AND In_Spells = 1
    """
    result = api.execute_warehouse_query(query)
    return result[0][0]


def our_count_all_time():
    return TransferHistory.objects.all().count()


def upstream_count_updated_last_month():
    last_month = datetime.datetime.now() - datetime.timedelta(30)
    api = ProdAPI()
    query = """
    SELECT COUNT(*) FROM INP.TRANSFER_HISTORY_EL_CID WITH (NOLOCK)
    WHERE LOCAL_PATIENT_IDENTIFIER is not null
    AND LOCAL_PATIENT_IDENTIFIER <> ''
    AND UPDATED_DATE >= @since
    AND In_TransHist = 1
    AND In_Spells = 1
    """
    result = api.execute_warehouse_query(
        query, params={"since": last_month}
    )
    return result[0][0]


def our_count_updated_last_month():
    last_month = timezone.make_aware(datetime.datetime.now()) - datetime.timedelta(30)
    return TransferHistory.objects.filter(updated_datetime__gte=last_month).count()


def upstream_transfers_last_month():
    last_month = datetime.datetime.now() - datetime.timedelta(30)
    api = ProdAPI()
    query = """
    SELECT COUNT(*) FROM INP.TRANSFER_HISTORY_EL_CID WITH (NOLOCK)
    WHERE LOCAL_PATIENT_IDENTIFIER is not null
    AND LOCAL_PATIENT_IDENTIFIER <> ''
    AND TRANS_HIST_START_DT_TM >= @since
    AND In_TransHist = 1
    AND In_Spells = 1
    """
    result = api.execute_warehouse_query(
        query, params={"since": last_month}
    )
    return result[0][0]


def our_transfers_last_month():
    last_month = timezone.make_aware(datetime.datetime.now()) - datetime.timedelta(30)
    return TransferHistory.objects.filter(
        transfer_start_datetime__gte=last_month
    ).count()


async def upstream_all_time():
    upstream_all_time = upstream_count_all_time()
    our_all_time = our_count_all_time()
    diff_all_time = our_all_time - upstream_all_time
    return f"All time:\t us {our_all_time}, them {upstream_all_time}, diff {diff_all_time}"


async def updated_last_month():
    upstream_count_updated_lm = upstream_count_updated_last_month()
    our_count_updated_lm = our_count_updated_last_month()
    diff_updated_lm = our_count_updated_lm - upstream_count_updated_lm
    return f"Updated last month:\t us {our_count_updated_lm}, them {upstream_count_updated_lm}, diff {diff_updated_lm}"


async def transfers_last_month():
    upstream_transfers_lm = upstream_transfers_last_month()
    our_transfers_lm = our_transfers_last_month()
    diff_transfers_lm = our_transfers_lm - upstream_transfers_lm
    return f"Transfers last month:\t us {our_transfers_lm}, them {upstream_transfers_lm}, diff {diff_transfers_lm}"


async def main():
    result = await asyncio.gather(upstream_all_time(), updated_last_month(), transfers_last_month())
    return result



class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        report = loop.run_until_complete(main())
        send_report(report)
