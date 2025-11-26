"""
Models for the elCID EPMA plugin
"""
from django.db import models
from opal.models import Patient, PatientSubrecord


class EPMAStatus(PatientSubrecord):
    _is_singleton = True

    has_epma = models.BooleanField(default=False)


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

    FIELDS_TO_SERIALIZE = [
        "o_encntr_id",
        "o_order_id",
        "e_finnumber",
        "e_create_dt_tm",
        "e_encntr_type_desc",  # Inpatient
        "e_treatmentfunction", # General Internal  Medicine
        "e_mainspecialty",     # General Internal  Medicine
        "e_loc_facility_desc", # RF
        "e_building",          # RFH
        "e_warddisplay",       # RF-8 EASt
        "e_leadconsultant",    # Initials, name
        "o_catalog_cd",        #  123456
        "o_catalog_type_desc", # Pharmacy
        "o_order_mnemonic",    # Sodium Chloride 0.9% Intravenous Solution 1,000 ML
        "o_cki_mltmlink",      # MUL.MMDC!5902
        "drug_identifier",     # d00088
        "o_orig_order_dt_tm",
        "oa_firstactionpersonnelname",
        "oa_firstpersonnelposition", # Clinical Practitioner Access Role
        "o_status_desc",       # Completed / Discontinued
        "o_discontinue_ind",   # 1 / 0
        "o_clinical_display_line",
        "o_order_signed_date_tm",
        "o_start_dt_tm",
        "o_stop_dt_tm",
        "o_orig_ord_as_flag",
        "o_need_rx_verify_ind",
        "o_template_order_flag",
        "o_active_status_prsnl_id",
        "o_last_action_sequence",
        "o_updt_dt_tm",
        "o_synonym_id",
        "ord_cat_syn_cki",
    ]

    def to_dict(self):
        data = {k: getattr(self, k) for k in self.FIELDS_TO_SERIALIZE}

        data['categories'] = []

        lookup = EPMATherapeuticClassLookup.objects.filter(
            mcdx_drug_identifier=self.drug_identifier).first()
        if lookup:
            data['categories'] = lookup.category_list()

        data['detail'] = [d.to_dict() for d in EPMAMedOrderDetail.objects.filter(epmamedorder=self)]

        return data

    def get_dose(self):
        """
        Look up dose information from Med order detail
        """
        dose = EPMAMedOrderDetail.objects.filter(epmamedorder=self, oe_field_meaning='STRENGTHDOSE')
        unit = EPMAMedOrderDetail.objects.filter(epmamedorder=self, oe_field_meaning='STRENGTHDOSEUNIT')

        dose_elements = []
        if dose.exists():
            dose_elements.append(dose.first().oe_field_display_value)

            if unit.exists():
                dose_elements.append(unit.first().oe_field_display_value)

            return ' '.join(dose_elements)

        return ''



class EPMAMedOrderDetail(models.Model):
    created_in_elcid = models.DateTimeField(auto_now_add=True)
    order_id = models.CharField(max_length=256, blank=True, null=True)
    epmamedorder = models.ForeignKey(EPMAMedOrder, on_delete=models.CASCADE)
    action_sequence = models.CharField(max_length=256, blank=True, null=True)
    detail_sequence = models.CharField(max_length=256, blank=True, null=True)
    oe_field_id = models.CharField(max_length=256, blank=True, null=True)
    oe_field_meaning = models.CharField(max_length=256, blank=True, null=True)
    oe_field_display_value = models.CharField(max_length=256, blank=True, null=True)
    oe_field_dt_tm_value = models.DateTimeField(blank=True, null=True)
    updt_dt_tm = models.DateTimeField(blank=True, null=True)
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

    FIELDS_TO_SERIALIZE = [
        "action_sequence",
        "detail_sequence",
        "oe_field_id",
        "oe_field_meaning",
        "oe_field_display_value",
        "oe_field_dt_tm_value",
    ]

    def to_dict(self):
        return {k: getattr(self, k) for k in self.FIELDS_TO_SERIALIZE}



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

    def category_list(self):
        """
        Return non-blank category lists
        """
        return [
            c for c in [self.multum_hierarchy_3,
                        self.multum_hierarchy_2,
                        self.multum_hierarchy_1,
                        self.multum_hierarchy_1a]
            if c
        ]
