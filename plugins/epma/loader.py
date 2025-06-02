"""
Load scripts for the EPMA module
"""
from django.db import transaction
from django.db.models import DateTimeField
from django.utils import timezone

from elcid.models import Demographics
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.epma.models import (
    EPMAMedOrder,
    EPMAMedOrderDetail,
    EPMATherapeuticClassLookup,
    EPMAStatus
)


Q_GET_MEDS_FOR_MRN = """
SELECT * FROM
CERNERRFG.EPMA_MedOrder
WHERE
LOCALPATIENTID = @mrn
"""

Q_GET_DETAILS_FOR_MRN = """
SELECT * FROM
CERNERRFG.EPMA_MedOrderDetail
FULL OUTER JOIN CERNERRFG.EPMA_MedOrder ON CERNERRFG.EPMA_MedOrderDetail.ORDER_ID = CERNERRFG.EPMA_MedOrder.O_ORDER_ID
WHERE
CERNERRFG.EPMA_MedOrder.LOCALPATIENTID = @MRN
"""

Q_SELECT_LOOKUP = """
SELECT * FROM CERNERRFG.EPMA_TherapeuticClassLookup
"""

def cast_to_instance(instance, row):
    """
    Given an INSTANCE of EPMAMedOrder or EPMAMedOrderDetail and a ROW
    from the upstream table, set the values from the upstream table
    on the local instance, ready to save to our database
    """
    for k, v in row.items():

        if k not in instance.UPSTREAM_FIELDS_TO_MODEL_FIELDS:
            continue # FULL OUTER JOIN SELECT * gives you the other model

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

def load_epmatherapeuticclasslookup():
    """
    There aren't many of these so just delete and recreate
    """
    EPMATherapeuticClassLookup.objects.all().delete()

    api = ProdAPI()
    query_results = api.execute_epma_query(Q_SELECT_LOOKUP)

    lookups = []
    for row in query_results:
        lookup = EPMATherapeuticClassLookup()
        lookup = cast_to_instance(lookup, row)
        lookups.append(lookup)
    EPMATherapeuticClassLookup.objects.bulk_create(lookups)


def load_meds_for_patient(patient):
    """
    Given a PATIENT, fetch all medications from the EPMA database
    """
    api = ProdAPI()
    mrn = patient.demographics().hospital_number
    other_mrns = list(
        patient.mergedmrn_set.values_list('mrn', flat=True)
    )
    mrns = [mrn] + other_mrns

    order_results = []
    order_detail_results = []

    for mrn in mrns:
        # result = api.execute_epma_query(Q_GET_MEDS_FOR_MRN, params={'mrn': mrn})
        # order_results.extend(result)

        detail_result = api.execute_epma_query(Q_GET_DETAILS_FOR_MRN, params={'mrn': mrn})
        order_detail_results.extend(detail_result)

   orders = []

    for row in order_results:
        order = EPMAMedOrder(patient_id=patient.id)
        order = cast_to_instance(order, row)
        orders.append(order)

    EPMAMedOrder.objects.bulk_create(orders)

    # if len(orders) > 0:
    #     EPMAStatus.objects.filter(patient=patient).update(has_epma=True)

    # order_details = []
    # for row in order_detail_results:
    #     # order = EPMAMedOrder.objects.get(o_order_id=row['ORDER_ID'])
    #     order_detail = EPMAMedOrder(patient_id=patient.id)
    #     order_detail = cast_to_instance(order_detail, row)
    #     order_details.append(order_detail)

    # EPMAMedOrderDetail.objects.bulk_create(order_details)

    return


# WIP Implementation 1


class Hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


def query_med_orders_since(since):
    api = ProdAPI()
    query = """
    SELECT * FROM CERNERRFG.EPMA_MedOrder
    WHERE LOAD_DT_TM > @since
    """
    return api.execute_epma_query(query, params={"since": since})


def query_med_order_details_since(since):
    api = ProdAPI()
    query = """
    SELECT * FROM CERNERRFG.EPMA_MedOrderDetail
    WHERE LOAD_DT_TM > @since
    """
    return api.execute_epma_query(query, params={"since": since})


def query_med_order_details_from_order_ids(order_ids):
    api = ProdAPI()
    order_dict = {f"order_{idx}": i for idx, i in enumerate(order_ids)}
    order_param_names = [f"@{i}" for i in list(order_dict.keys())]
    query = f"""
    SELECT * FROM CERNERRFG.EPMA_MedOrderDetail
    WHERE ORDER_ID IN ({",".join(order_param_names)})
    """
    return api.execute_epma_query(query, params=order_dict)


@transaction.atomic
def load_med_orders_since(since):
    query_result = query_med_orders_since(since)
    if not query_result:
        return
    hospital_nunbers = [
        i["LOCALPATIENTID"] for i in query_result if i["LOCALPATIENTID"]
    ]
    our_hns = set(Demographics.objects.filter(
        hospital_number__in=hospital_nunbers
    ).values_list('hospital_number', flat=True))
    query_result = [
        i for i in query_result if i["LOCALPATIENTID"] in our_hns
    ]

    # order id is not unique, mrn order id is
    mrns_and_order_ids = [
        (
            i["LOCALPATIENTID"],
            i["O_ORDER_ID"],
        )
        for i in query_result
    ]
    order_ids = [i[1] for i in mrns_and_order_ids]

    our_orders = EPMAMedOrder.objects.filter(
        o_order_id__in=order_ids
    ).prefetch_related(
        "patient__demographics_set"
    )

    our_mrns_and_order_ids_to_ids = {}
    for our_order in our_orders:
        demographics = our_order.patient.demographics_set.all()[0]
        key = (
            demographics.hospital_number,
            our_order.o_order_id,
        )
        our_mrns_and_order_ids_to_ids[key] = our_order.id

    to_delete = []
    for mrn_and_order_id in mrns_and_order_ids:
        our_id = our_mrns_and_order_ids_to_ids.get(mrn_and_order_id)
        if our_id:
            to_delete.append(our_id)
    EPMAMedOrder.objects.filter(id__in=to_delete).delete()
    orders = []
    for row in query_result:
        hn = row["LOCALPATIENTID"]
        demographics = Demographics.objects.filter(
            hospital_number=hn
        )
        for demo in demographics:
            order = EPMAMedOrder(patient_id=demo.patient_id)
            order = cast_to_instance(order, row)
            orders.append(order)
    EPMAMedOrder.objects.bulk_create(orders)

    order_details = [Hashabledict(i) for i in query_med_order_details_since(since)]
    patient_order_details = []
    for i in range(0, len(order_ids), 100):
        patient_order_details.extend(
            Hashabledict(row) for row in query_med_order_details_from_order_ids(order_ids[i:i+100])
        )
    detail_rows = list(set(order_details) | set(patient_order_details))
    order_details = []
    for detail_row in detail_rows:
        orders = EPMAMedOrder.objects.filter(
            o_order_id=detail_row["ORDER_ID"]
        )
        for order in orders:
            order_detail = EPMAMedOrderDetail(epmamedorder=order)
            order_detail = cast_to_instance(order_detail, detail_row)
            order_details.append(order_detail)
    EPMAMedOrderDetail.objects.bulk_create(order_details)
