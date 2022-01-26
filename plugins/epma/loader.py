from collections import defaultdict
import datetime
from django.db import transaction
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from django.db.models import DateTimeField
from django.utils import timezone
from elcid.models import Demographics
from plugins.epma.models import (
    EPMAMedOrder,
    EPMAMedOrderDetail,
    EPMATherapeuticClassLookup,
)


def query_med_orders_since(since, to):
    api = ProdAPI()
    query = """
    SELECT * FROM CERNERRFG.EPMA_MedOrder
    WHERE LOAD_DT_TM >= @since
    AND LOAD_DT_TM < @to
    """
    return api.execute_epma_query(query, params={"since": since})


def query_med_order_details_since(since):
    api = ProdAPI()
    query = """
    SELECT * FROM CERNERRFG.EPMA_MedOrderDetail
    WHERE ORDER_ID IN (
        SELECT O_ORDER_ID FROM CERNERRFG.EPMA_MedOrder
        WHERE LOAD_DT_TM >= @since
        AND LOAD_DT_TM < @to
    )
    """
    return api.execute_epma_query(query, params={"since": since})


def cast_to_instance(instance, row):
    for k, v in row.items():
        if v:  # Ignore empty values
            fieldtype = type(
                instance.__class__._meta.get_field(
                    instance.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k]
                )
            )
            if fieldtype == DateTimeField:
                v = timezone.make_aware(v)
            setattr(instance, instance.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k], v)
    return instance


@transaction.atomic
def load_med_orders_since(since, to):
    if to is None:
        to = datetime.datetime.max
    query_result = query_med_orders_since(since, to)
    details = query_med_order_details_since(since, to)
    if not query_result:
        return
    hospital_nunbers = set([
        i["LOCALPATIENTID"] for i in query_result if i["LOCALPATIENTID"] if i["LOCALPATIENTID"]
    ])
    our_hospital_number_to_patients = defaultdict(list)
    demographics = Demographics.objects.filter(
        hospital_number__in=hospital_nunbers
    ).select_related('patient')
    for demo in demographics:
        our_hospital_number_to_patients[demo.hospital_number].append(
            demo.patient
        )
    query_result = [
        i for i in query_result if i["LOCALPATIENTID"] in our_hospital_number_to_patients
    ]
    EPMAMedOrder.objects.filter(
        o_order_id__in=[i["O_ORDER_ID"] for i in query_result]
    ).delete()

    orders = []

    for row in query_result:
        patients = our_hospital_number_to_patients[row["LOCALPATIENTID"]]
        for patient in patients:
            order = EPMAMedOrder(patient=patient)
            order = cast_to_instance(order, row)
            orders.append(order)

    EPMAMedOrder.objects.bulk_create(orders, batch_size=500)

    details_by_order_id = defaultdict(list)
    for detail in details:
        details_by_order_id[detail["ORDER_ID"]].append(detail)

    details_to_create = []
    for order_id, details in details_by_order_id.items():
        epma_orders = EPMAMedOrder.objects.filter(o_order_id=order_id)
        for order in epma_orders:
            for detail in details:
                order_detail = EPMAMedOrderDetail(epmamedorder=order)
                order_detail = cast_to_instance(order_detail, detail)
                details_to_create.append(order_detail)

    EPMAMedOrderDetail.objects.bulk_create(details_to_create, batch_size=500)


def query_epmatherapeuticclasslookup():
    api = ProdAPI()
    query = """
    SELECT * FROM CERNERRFG.EPMA_TherapeuticClassLookup
    """
    return api.execute_epma_query(query)


@transaction.atomic
def load_epmatherapeuticclasslookup():
    """
    There aren't many of these so just delete and recreate
    """
    EPMATherapeuticClassLookup.objects.all().delete()
    query_results = query_epmatherapeuticclasslookup()
    lookups = []
    for row in query_results:
        lookup = EPMATherapeuticClassLookup()
        lookup = cast_to_instance(lookup, row)
        lookups.append(lookup)
    EPMATherapeuticClassLookup.objects.bulk_create(lookups)
