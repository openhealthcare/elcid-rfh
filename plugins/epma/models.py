from django.db import models
from opal.models import Patient


def serialize_model(instance):
    result = {}
    fields = instance._meta.get_fields()
    for field in fields:
        if not field.is_relation:
            result[field.name] = getattr(instance, field.name)
    return result


class EPMAMedOrder(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    created_in_elcid = models.DateTimeField(auto_now_add=True)
    localpatientid = models.CharField(max_length=256)
    o_encntr_id = models.CharField(max_length=256)
    o_order_id = models.CharField(max_length=256)
    e_finnumber = models.CharField(max_length=256, blank=True, null=True)
    e_create_dt_tm = models.DateTimeField(blank=True, null=True)
    e_encntr_type_desc = models.CharField(max_length=256, blank=True, null=True)
    e_treatmentfunction = models.CharField(max_length=256, blank=True, null=True)
    e_mainspecialty = models.CharField(max_length=256, blank=True, null=True)
    e_loc_facility_desc = models.CharField(max_length=256, blank=True, null=True)
    e_building = models.CharField(max_length=256, blank=True, null=True)
    e_warddisplay = models.CharField(max_length=256, blank=True, null=True)
    e_leadconsultant = models.CharField(max_length=256, blank=True, null=True)
    o_catalog_cd = models.CharField(max_length=256)
    o_catalog_type_desc = models.CharField(max_length=256, blank=True, null=True)
    o_order_mnemonic = models.CharField(max_length=256, blank=True, null=True)
    o_cki_mltmlink = models.CharField(max_length=256, blank=True, null=True)
    drug_identifier = models.CharField(max_length=256, blank=True, null=True)
    o_orig_order_dt_tm = models.DateTimeField(blank=True, null=True)
    oa_firstactionpersonnelname = models.CharField(
        max_length=256, blank=True, null=True
    )
    oa_firstpersonnelposition = models.CharField(max_length=256, blank=True, null=True)
    o_status_desc = models.CharField(max_length=256, blank=True, null=True)
    o_discontinue_ind = models.CharField(max_length=256, blank=True, null=True)
    o_clinical_display_line = models.TextField(blank=True, null=True)
    o_order_signed_date_tm = models.DateTimeField(blank=True, null=True)
    o_start_dt_tm = models.CharField(max_length=256, blank=True, null=True)
    o_stop_dt_tm = models.CharField(max_length=256, blank=True, null=True)
    o_orig_ord_as_flag = models.CharField(max_length=256, blank=True, null=True)
    o_need_rx_verify_ind = models.CharField(max_length=256, blank=True, null=True)
    o_template_order_flag = models.CharField(max_length=256, blank=True, null=True)
    o_active_status_prsnl_id = models.CharField(max_length=256)
    o_last_action_sequence = models.CharField(max_length=256, blank=True, null=True)
    o_updt_dt_tm = models.DateTimeField()
    o_synonym_id = models.CharField(max_length=256)
    ord_cat_syn_cki = models.CharField(max_length=256, blank=True, null=True)
    domain_name = models.CharField(max_length=256, blank=True, null=True)
    load_dt_tm = models.DateTimeField(blank=True, null=True)
    o_start_dt_tm = models.DateTimeField(blank=True, null=True)

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        "LOCALPATIENTID": "localpatientid",
        "O_ENCNTR_ID":  "o_encntr_id",
        "O_ORDER_ID":  "o_order_id",
        "E_FINNUMBER":  "e_finnumber",
        "E_CREATE_DT_TM":  "e_create_dt_tm",
        "E_ENCNTR_TYPE_DESC":  "e_encntr_type_desc",
        "E_TREATMENTFUNCTION":  "e_treatmentfunction",
        "E_MAINSPECIALTY":  "e_mainspecialty",
        "E_LOC_FACILITY_DESC":  "e_loc_facility_desc",
        "E_BUILDING":  "e_building",
        "E_WARDDISPLAY":  "e_warddisplay",
        "E_LEADCONSULTANT":  "e_leadconsultant",
        "O_CATALOG_CD":  "o_catalog_cd",
        "O_CATALOG_TYPE_DESC":  "o_catalog_type_desc",
        "O_ORDER_MNEMONIC":  "o_order_mnemonic",
        "O_CKI_MLTMLINK":  "o_cki_mltmlink",
        "DRUG_IDENTIFIER":  "drug_identifier",
        "O_ORIG_ORDER_DT_TM":  "o_orig_order_dt_tm",
        "OA_FirstActionPersonnelName":  "oa_firstactionpersonnelname",
        "OA_FirstPERSONNELPOSITION":  "oa_firstpersonnelposition",
        "O_STATUS_DESC":  "o_status_desc",
        "O_DISCONTINUE_IND":  "o_discontinue_ind",
        "O_CLINICAL_DISPLAY_LINE":  "o_clinical_display_line",
        "O_ORDER_SIGNED_DATE_TM":  "o_order_signed_date_tm",
        "O_START_DT_TM":  "o_start_dt_tm",
        "O_STOP_DT_TM":  "o_stop_dt_tm",
        "O_ORIG_ORD_AS_FLAG":  "o_orig_ord_as_flag",
        "O_NEED_RX_VERIFY_IND":  "o_need_rx_verify_ind",
        "O_TEMPLATE_ORDER_FLAG":  "o_template_order_flag",
        "O_ACTIVE_STATUS_PRSNL_ID":  "o_active_status_prsnl_id",
        "O_LAST_ACTION_SEQUENCE":  "o_last_action_sequence",
        "O_UPDT_DT_TM":  "o_updt_dt_tm",
        "O_SYNONYM_ID":  "o_synonym_id",
        "ORD_CAT_SYN_CKI":  "ord_cat_syn_cki",
        "DOMAIN_NAME":  "domain_name",
        "LOAD_DT_TM":  "load_dt_tm",
    }

    def to_dict(self):
        as_dict = serialize_model(self)
        order_details = self.epmamedorderdetail_set.all().order_by(
            'action_sequence', 'detail_sequence'
        )
        as_dict["details"] = [
            serialize_model(i) for i in order_details
        ]
        return as_dict


class EPMAMedOrderDetail(models.Model):
    created_in_elcid = models.DateTimeField(auto_now_add=True)
    order_id = models.CharField(max_length=256)
    epmamedorder = models.ForeignKey(EPMAMedOrder, on_delete=models.CASCADE)
    action_sequence = models.CharField(max_length=256)
    detail_sequence = models.CharField(max_length=256)
    oe_field_id = models.CharField(max_length=256)
    oe_field_meaning = models.CharField(max_length=256, blank=True, null=True)
    oe_field_display_value = models.CharField(max_length=256, blank=True, null=True)
    oe_field_dt_tm_value = models.DateTimeField(blank=True, null=True)
    updt_dt_tm = models.DateTimeField()
    load_dt_tm = models.DateTimeField(blank=True, null=True)

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        "ORDER_ID":  "order_id",
        "ACTION_SEQUENCE":  "action_sequence",
        "DETAIL_SEQUENCE":  "detail_sequence",
        "OE_FIELD_ID":  "oe_field_id",
        "OE_FIELD_MEANING":  "oe_field_meaning",
        "OE_FIELD_DISPLAY_VALUE":  "oe_field_display_value",
        "OE_FIELD_DT_TM_VALUE":  "oe_field_dt_tm_value",
        "UPDT_DT_TM":  "updt_dt_tm",
        "LOAD_DT_TM":  "load_dt_tm",
    }


class EPMATherapeuticClassLookup(models.Model):
    created_in_elcid = models.DateTimeField(auto_now_add=True)
    mcdx_drug_identifier = models.CharField(max_length=256)
    mcdx_multum_category_id = models.CharField(max_length=256)
    mcdx_updt_dt_tm = models.CharField(max_length=256)
    multum_hierarchy_1a = models.CharField(max_length=256, blank=True, null=True)
    multum_hierarchy_1 = models.CharField(max_length=256, blank=True, null=True)
    multum_hierarchy_2 = models.CharField(max_length=256, blank=True, null=True)
    multum_hierarchy_3 = models.CharField(max_length=256, blank=True, null=True)
    mdc_updt_dt_tm = models.DateTimeField(blank=True, null=True)
    load_dt_tm = models.DateTimeField(blank=True, null=True)

    UPSTREAM_FIELDS_TO_MODEL_FIELDS = {
        "MCDX_DRUG_IDENTIFIER":  "mcdx_drug_identifier",
        "MCDX_MULTUM_CATEGORY_ID":  "mcdx_multum_category_id",
        "MCDX_UPDT_DT_TM":  "mcdx_updt_dt_tm",
        "MULTUM_HIERARCHY_1A":  "multum_hierarchy_1a",
        "MULTUM_HIERARCHY_1":  "multum_hierarchy_1",
        "MULTUM_HIERARCHY_2":  "multum_hierarchy_2",
        "MULTUM_HIERARCHY_3":  "multum_hierarchy_3",
        "MDC_UPDT_DT_TM":  "mdc_updt_dt_tm",
        "LOAD_DT_TM":  "load_dt_tm",
    }
