"""
elCID implementation specific models!
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
# from lab import models as lmodels

from jsonfield import JSONField

import opal.models as omodels

from opal.models import (
    EpisodeSubrecord, PatientSubrecord, Episode, ExternallySourcedModel
)
from opal.core.fields import ForeignKeyOrFreeText
from opal.core import lookuplists


def get_for_lookup_list(model, values):
    ct = ContentType.objects.get_for_model(model)
    return model.objects.filter(
        models.Q(name__in=values) |
        models.Q(synonyms__name__in=values, synonyms__content_type=ct)
    )


class Demographics(PatientSubrecord, ExternallySourcedModel):
    _is_singleton = True
    _icon = 'fa fa-user'

    hospital_number = models.CharField(max_length=255, blank=True)
    nhs_number = models.CharField(max_length=255, blank=True, null=True)

    surname = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    title = ForeignKeyOrFreeText(omodels.Title)
    date_of_birth = models.DateField(null=True, blank=True)
    marital_status = ForeignKeyOrFreeText(omodels.MaritalStatus)
    religion = models.CharField(max_length=255, blank=True, null=True)
    date_of_death = models.DateField(null=True, blank=True)
    post_code = models.CharField(max_length=20, blank=True, null=True)
    gp_practice_code = models.CharField(max_length=20, blank=True, null=True)
    birth_place = ForeignKeyOrFreeText(omodels.Destination)
    ethnicity = ForeignKeyOrFreeText(omodels.Ethnicity)
    death_indicator = models.BooleanField(default=False)

    # not strictly correct, but it will be updated when opal core models
    # are updated
    sex = ForeignKeyOrFreeText(omodels.Gender)

    def set_death_indicator(self, value, *args, **kwargs):
        if not value:
            return

    pid_fields = (
        'hospital_number', 'nhs_number', 'surname', 'first_name',
        'middle_name', 'post_code',
    )

    class Meta:
        verbose_name_plural = "Demographics"

    @classmethod
    def get_form_template(cls, patient_list=None, episode_type=None):
        if settings.GLOSS_ENABLED:
            return super(Demographics, cls).get_form_template(patient_list=None, episode_type=None)
        else:
            return "forms/demographics_form_pre_gloss.html"


class ContactDetails(PatientSubrecord):
    _is_singleton = True
    _advanced_searchable = False
    _icon = 'fa fa-phone'

    address_line1 = models.CharField("Address line 1", max_length = 45,
                                     blank=True, null=True)
    address_line2 = models.CharField("Address line 2", max_length = 45,
                                     blank=True, null=True)
    city          = models.CharField(max_length = 50, blank = True)
    county        = models.CharField("County", max_length = 40,
                                     blank=True, null=True)
    post_code     = models.CharField("Post Code", max_length = 10,
                                     blank=True, null=True)
    tel1          = models.CharField(blank=True, null=True, max_length=50)
    tel2          = models.CharField(blank=True, null=True, max_length=50)

    class Meta:
        verbose_name_plural = "Contact details"


class Carers(PatientSubrecord):
    _is_singleton = True
    _advanced_searchable = False
    _icon = 'fa fa-users'

    gp    = models.TextField(blank=True, null=True)
    nurse = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Carers"


class DuplicatePatient(PatientSubrecord):
    _no_admin = True
    _icon = 'fa fa-clone'
    _advanced_searchable = False
    reviewed = models.BooleanField(default=False)
    merged = models.BooleanField(default=False)

    def icon(self):
        return self._icon


class LocationCategory(lookuplists.LookupList):
    pass


class Provenance(lookuplists.LookupList):
    pass


class Location(EpisodeSubrecord):
    _is_singleton = True
    _icon = 'fa fa-map-marker'

    category = ForeignKeyOrFreeText(LocationCategory)
    provenance = ForeignKeyOrFreeText(Provenance)
    hospital = ForeignKeyOrFreeText(omodels.Hospital)
    ward = ForeignKeyOrFreeText(omodels.Ward)
    bed = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        try:
            demographics = self.episode.patient.demographics_set.get()
            return u'Location for {0}({1}) {2} {3} {4} {5}'.format(
                demographics.name,
                demographics.hospital_number,
                self.category,
                self.hospital,
                self.ward,
                self.bed
            )
        except:
            return 'demographics'


class Result(PatientSubrecord):
    _icon = 'fa fa-crosshairs'

    lab_number = models.CharField(max_length=255, blank=True, null=True)
    profile_code = models.CharField(max_length=255, blank=True, null=True)
    external_identifier = models.CharField(max_length=255, blank=True, null=True)
    profile_description = models.CharField(max_length=255, blank=True, null=True)
    request_datetime = models.DateTimeField(blank=True, null=True)
    observation_datetime = models.DateTimeField(blank=True, null=True)
    last_edited = models.DateTimeField(blank=True, null=True)
    result_status = models.CharField(max_length=255, blank=True, null=True)
    observations = JSONField(blank=True, null=True)

    def update_from_dict(self, data, *args, **kwargs):
        if "id" not in data:
            if "patient_id" not in data:
                raise ValueError("no patient id found for result in %s" % data)
            if "external_identifier" in data and data["external_identifier"]:
                existing = Result.objects.filter(
                    external_identifier=data["external_identifier"],
                    patient=data["patient_id"]
                ).first()

                if existing:
                    data["id"] = existing.id

        super(Result, self).update_from_dict(data, *args, **kwargs)


class InfectionSource(lookuplists.LookupList):
    pass


class Infection(EpisodeSubrecord):
    _title = 'Infection related issues'
    _icon = 'fa fa-eyedropper'
    # this needs to be fixed
    source = ForeignKeyOrFreeText(InfectionSource)
    site = models.CharField(max_length=255, blank=True)


class MedicalProcedure(lookuplists.LookupList):
    pass


class SurgicalProcedure(lookuplists.LookupList):
    pass


class Procedure(EpisodeSubrecord):
    _title = 'Operation / Procedures'
    _icon = 'fa fa-sitemap'
    date = models.DateField(blank=True, null=True)
    medical_procedure = ForeignKeyOrFreeText(MedicalProcedure)
    surgical_procedure = ForeignKeyOrFreeText(SurgicalProcedure)


class PresentingComplaint(EpisodeSubrecord):
    _title = 'Presenting Complaint'
    _icon = 'fa fa-stethoscope'

    symptom = ForeignKeyOrFreeText(omodels.Symptom)
    symptoms = models.ManyToManyField(omodels.Symptom, related_name="presenting_complaints")
    duration = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    def set_symptom(self, *args, **kwargs):
        # ignore symptom for the time being
        pass

    def to_dict(self, user):
        field_names = self.__class__._get_fieldnames_to_serialize()
        result = {
            i: getattr(self, i) for i in field_names if not i == "symptoms"
        }
        result["symptoms"] = list(self.symptoms.values_list("name", flat=True))
        return result

    @classmethod
    def _get_fieldnames_to_serialize(cls):
        field_names = super(PresentingComplaint, cls)._get_fieldnames_to_serialize()
        removed_fields = {u'symptom_fk_id', 'symptom_ft', 'symptom'}
        field_names = [i for i in field_names if i not in removed_fields]
        return field_names


class PrimaryDiagnosisCondition(lookuplists.LookupList): pass

class PrimaryDiagnosis(EpisodeSubrecord):
    """
    This is the confirmed primary diagnosisa
    """
    _is_singleton = True
    _title = 'Primary Diagnosis'
    _icon = 'fa fa-eye'

    condition = ForeignKeyOrFreeText(PrimaryDiagnosisCondition)
    confirmed = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Primary diagnoses"


class Consultant(lookuplists.LookupList): pass

class ConsultantAtDischarge(EpisodeSubrecord):
    _title = 'Consultant At Discharge'
    _is_singleton = True
    consultant = ForeignKeyOrFreeText(Consultant)


class SecondaryDiagnosis(EpisodeSubrecord):
    """
    This is a confirmed diagnosis at discharge time.
    """
    _title = 'Secondary Diagnosis'
    condition   = ForeignKeyOrFreeText(omodels.Condition)
    co_primary = models.NullBooleanField(default=False)

    class Meta:
        verbose_name_plural = "Secondary diagnoses"


class Diagnosis(EpisodeSubrecord):
    """
    This is a working-diagnosis list, will often contain things that are
    not technically diagnoses, but is for historical reasons, called diagnosis.
    """
    _title = 'Diagnosis / Issues'
    _sort = 'date_of_diagnosis'
    _icon = 'fa fa-stethoscope'

    condition         = ForeignKeyOrFreeText(omodels.Condition)
    provisional       = models.NullBooleanField()
    details           = models.CharField(max_length=255, blank=True)
    date_of_diagnosis = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return u'Diagnosis of {0} - {1}'.format(
            self.condition,
            self.date_of_diagnosis
            )

    class Meta:
        verbose_name_plural = "Diagnoses"


class PastMedicalHistory(EpisodeSubrecord):
    _title = 'PMH'
    _sort = 'year'
    _icon = 'fa fa-history'

    condition = ForeignKeyOrFreeText(omodels.Condition)
    year      = models.CharField(max_length=200, blank=True)
    details   = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = "Past medical histories"


class GeneralNote(EpisodeSubrecord):
    _title = 'General Notes'
    _sort  = 'date'
    _icon = 'fa fa-info-circle'

    date    = models.DateField(null=True, blank=True)
    comment = models.TextField()


class Travel(EpisodeSubrecord):
    _icon = 'fa fa-plane'

    destination         = ForeignKeyOrFreeText(omodels.Destination)
    dates               = models.CharField(max_length=255, blank=True)
    reason_for_travel   = ForeignKeyOrFreeText(omodels.Travel_reason)
    did_not_travel      = models.NullBooleanField(default=False)
    specific_exposures  = models.CharField(max_length=255, blank=True)
    malaria_prophylaxis = models.NullBooleanField(default=False)
    malaria_drug        = ForeignKeyOrFreeText(omodels.Antimicrobial)
    malaria_compliance  = models.CharField(max_length=200, blank=True, null=True)


class Iv_stop(lookuplists.LookupList):
    class Meta:
        verbose_name = "IV stop"


class Drug_delivered(lookuplists.LookupList):
    class Meta:
        verbose_name_plural = "Drugs delivered"


class Antimicrobial(EpisodeSubrecord):
    _title = 'Antimicrobials'
    _sort = 'start_date'
    _icon = 'fa fa-flask'
    _modal = 'lg'

    drug          = ForeignKeyOrFreeText(omodels.Antimicrobial)
    dose          = models.CharField(max_length=255, blank=True)
    route         = ForeignKeyOrFreeText(omodels.Antimicrobial_route)
    start_date    = models.DateField(null=True, blank=True)
    end_date      = models.DateField(null=True, blank=True)
    delivered_by  = ForeignKeyOrFreeText(Drug_delivered)
    reason_for_stopping = ForeignKeyOrFreeText(Iv_stop)
    adverse_event = ForeignKeyOrFreeText(omodels.Antimicrobial_adverse_event)
    comments      = models.TextField(blank=True, null=True)
    frequency     = ForeignKeyOrFreeText(omodels.Antimicrobial_frequency)
    no_antimicrobials = models.NullBooleanField(default=False)


class Allergies(PatientSubrecord, ExternallySourcedModel):
    _icon = 'fa fa-warning'

    drug        = ForeignKeyOrFreeText(omodels.Antimicrobial)
    provisional = models.NullBooleanField()
    details     = models.CharField(max_length=255, blank=True)

    # previously called drug this is the name of the problematic substance
    allergy_description = models.CharField(max_length=255, blank=True)
    allergy_type_description = models.CharField(max_length=255, blank=True)
    certainty_id = models.CharField(max_length=255, blank=True)
    certainty_description = models.CharField(max_length=255, blank=True)
    allergy_reference_name = models.CharField(max_length=255, blank=True)
    allergen_reference_system = models.CharField(max_length=255, blank=True)
    allergen_reference = models.CharField(max_length=255, blank=True)
    status_id = models.CharField(max_length=255, blank=True)
    status_description = models.CharField(max_length=255, blank=True)
    diagnosis_datetime = models.DateTimeField(null=True, blank=True)
    allergy_start_datetime = models.DateTimeField(null=True, blank=True)
    no_allergies = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Allergies"


class RenalFunction(lookuplists.LookupList):
    pass


class LiverFunction(lookuplists.LookupList):
    pass


class MicrobiologyInput(EpisodeSubrecord):
    _title = 'Clinical Advice'
    _sort = 'when'
    _icon = 'fa fa-comments'
    _modal = 'lg'
    _list_limit = 3
    _angular_service = 'MicrobiologyInput'

    when = models.DateTimeField(null=True, blank=True)
    initials = models.CharField(max_length=255, blank=True)
    reason_for_interaction = ForeignKeyOrFreeText(
        omodels.Clinical_advice_reason_for_interaction
    )
    infection_control = models.TextField(blank=True)
    clinical_discussion = models.TextField(blank=True)
    agreed_plan = models.TextField(blank=True)
    discussed_with = models.CharField(max_length=255, blank=True)
    clinical_advice_given = models.NullBooleanField()
    infection_control_advice_given = models.NullBooleanField()
    change_in_antibiotic_prescription = models.NullBooleanField()
    referred_to_opat = models.NullBooleanField()
    white_cell_count = models.IntegerField(null=True, blank=True)
    c_reactive_protein = models.CharField(max_length=255, blank=True)
    maximum_temperature = models.IntegerField(null=True, blank=True)
    renal_function = ForeignKeyOrFreeText(RenalFunction)
    liver_function = ForeignKeyOrFreeText(LiverFunction)

class Todo(EpisodeSubrecord):
    _title = 'To Do'
    _icon = 'fa fa-th-list'

    details = models.TextField(blank=True)

class Hiv_no(lookuplists.LookupList):
    class Meta:
        verbose_name = "HIV refusal reason"


class MicrobiologyTest(EpisodeSubrecord):
    _title = 'Investigations'
    _sort = 'date_ordered'
    _icon = 'fa fa-crosshairs'
    _modal = 'lg'

    test                  = models.CharField(max_length=255)
    alert_investigation   = models.BooleanField(default=False)
    date_ordered          = models.DateField(null=True, blank=True)
    details               = models.CharField(max_length=255, blank=True)
    microscopy            = models.CharField(max_length=255, blank=True)
    organism              = models.CharField(max_length=255, blank=True)
    sensitive_antibiotics = models.CharField(max_length=255, blank=True)
    resistant_antibiotics = models.CharField(max_length=255, blank=True)
    result                = models.CharField(max_length=255, blank=True)
    igm                   = models.CharField(max_length=20, blank=True)
    igg                   = models.CharField(max_length=20, blank=True)
    vca_igm               = models.CharField(max_length=20, blank=True)
    vca_igg               = models.CharField(max_length=20, blank=True)
    ebna_igg              = models.CharField(max_length=20, blank=True)
    hbsag                 = models.CharField(max_length=20, blank=True)
    anti_hbs              = models.CharField(max_length=20, blank=True)
    anti_hbcore_igm       = models.CharField(max_length=20, blank=True)
    anti_hbcore_igg       = models.CharField(max_length=20, blank=True)
    rpr                   = models.CharField(max_length=20, blank=True)
    tppa                  = models.CharField(max_length=20, blank=True)
    viral_load            = models.CharField(max_length=20, blank=True)
    parasitaemia          = models.CharField(max_length=20, blank=True)
    hsv                   = models.CharField(max_length=20, blank=True)
    vzv                   = models.CharField(max_length=20, blank=True)
    syphilis              = models.CharField(max_length=20, blank=True)
    c_difficile_antigen   = models.CharField(max_length=20, blank=True)
    c_difficile_toxin     = models.CharField(max_length=20, blank=True)
    species               = models.CharField(max_length=20, blank=True)
    hsv_1                 = models.CharField(max_length=20, blank=True)
    hsv_2                 = models.CharField(max_length=20, blank=True)
    enterovirus           = models.CharField(max_length=20, blank=True)
    cmv                   = models.CharField(max_length=20, blank=True)
    ebv                   = models.CharField(max_length=20, blank=True)
    influenza_a           = models.CharField(max_length=20, blank=True)
    influenza_b           = models.CharField(max_length=20, blank=True)
    parainfluenza         = models.CharField(max_length=20, blank=True)
    metapneumovirus       = models.CharField(max_length=20, blank=True)
    rsv                   = models.CharField(max_length=20, blank=True)
    adenovirus            = models.CharField(max_length=20, blank=True)
    norovirus             = models.CharField(max_length=20, blank=True)
    rotavirus             = models.CharField(max_length=20, blank=True)
    giardia               = models.CharField(max_length=20, blank=True)
    entamoeba_histolytica = models.CharField(max_length=20, blank=True)
    cryptosporidium       = models.CharField(max_length=20, blank=True)
    hiv_declined          = ForeignKeyOrFreeText(Hiv_no)
    spotted_fever_igm     = models.CharField(max_length=20, blank=True)
    spotted_fever_igg     = models.CharField(max_length=20, blank=True)
    typhus_group_igm      = models.CharField(max_length=20, blank=True)
    typhus_group_igg      = models.CharField(max_length=20, blank=True)
    scrub_typhus_igm      = models.CharField(max_length=20, blank=True)
    scrub_typhus_igg      = models.CharField(max_length=20, blank=True)


class Line(EpisodeSubrecord):
    _sort = 'insertion_datetime'
    _icon = 'fa fa-bolt'

    line_type = ForeignKeyOrFreeText(omodels.Line_type)
    site = ForeignKeyOrFreeText(omodels.Line_site)
    insertion_datetime = models.DateTimeField(blank=True, null=True)
    inserted_by = models.CharField(max_length=255, blank=True, null=True)
    external_length = models.CharField(max_length=255, blank=True, null=True)
    removal_datetime = models.DateTimeField(blank=True, null=True)
    complications = ForeignKeyOrFreeText(omodels.Line_complication)
    removal_reason = ForeignKeyOrFreeText(omodels.Line_removal_reason)
    special_instructions = models.TextField()
    button_hole = models.NullBooleanField()
    tunnelled_or_temp = models.CharField(max_length=200, blank=True, null=True)
    fistula = models.NullBooleanField(blank=True, null=True)
    graft = models.NullBooleanField(blank=True, null=True)


class Appointment(EpisodeSubrecord):
    _title = 'Upcoming Appointments'
    _sort = 'date'
    _icon = 'fa fa-calendar'
    _advanced_searchable = False

    appointment_type = models.CharField(max_length=200, blank=True, null=True)
    appointment_with = models.CharField(max_length=200, blank=True, null=True)
    date             = models.DateField(blank=True, null=True)

class BloodCultureSource(lookuplists.LookupList):
    pass

# class BloodCulture(lmodels.LabTestCollection, EpisodeSubrecord):
#     _icon = 'fa fa-crosshairs'
#     _title = 'Blood Culture'
#     _angular_service = 'BloodCultureRecord'
#
#     lab_number = models.CharField(max_length=255, blank=True)
#     date_ordered = models.DateField(null=True, blank=True)
#     date_positive = models.DateField(null=True, blank=True)
#     source = ForeignKeyOrFreeText(BloodCultureSource)
#
#     @classmethod
#     def _get_fieldnames_to_serialize(cls):
#         field_names = super(BloodCulture, cls)._get_fieldnames_to_serialize()
#         field_names.append("isolates")
#         return field_names
#
#     def update_from_dict(self, data, user, **kwargs):
#         isolates = data.pop("isolates", [])
#         existing = [i["id"] for i in isolates if "id" in i]
#         self.isolates.exclude(id__in=existing).delete()
#         kwargs.pop("fields", None)
#         fields = set(self.__class__._get_fieldnames_to_serialize())
#         fields.remove("isolates")
#         super(BloodCulture, self).update_from_dict(data, user, fields=fields, **kwargs)
#
#         for isolate in isolates:
#             isolate_id = isolate.get("id")
#
#             if isolate_id:
#                 blood_culture_isolate = self.isolates.get(
#                     id=isolate_id
#                 )
#             else:
#                 blood_culture_isolate = BloodCultureIsolate(
#                     blood_culture_id=self.id
#                 )
#
#             blood_culture_isolate.update_from_dict(isolate, user, **kwargs)
#
#     def get_isolates(self, user):
#         return [i.to_dict(user) for i in self.isolates.all()]
#
# class FishForm(object):
#     def get_result_look_up_list(self):
#         lookup_list = super(FishForm, self).get_result_look_up_list()
#         lookup_list.append("Not Done")
#         return lookup_list
#
#     def update_from_dict(self, data, user, **kwargs):
#         """
#             if there is no result or its not done, skip
#         """
#         result = data.get("result")
#         id_field = data.get("id")
#
#         if not result or result == "Not Done":
#             if id_field:
#                 lmodels.LabTest.objects.get(id=id_field).delete()
#             return
#
#         super(FishForm, self).update_from_dict(data, user, **kwargs)
#
#
# class GramStain(lmodels.LabTest):
#     class Meta:
#         proxy = True
#
#     RESULT_CHOICES = (
#         ("yeast", "Yeast",),
#         ("gram_positive_cocci_cluster", "Gram +ve Cocci Cluster",),
#         ("gram_positive_cocci_chains", "Gram +ve Cocci Chains",),
#         ("gram_negative_rods", "Gram -ve Rods",),
#         ("gram_negative_cocci", "Gram -ve Cocci",),
#         ("zn_stain", "ZN Stain",),
#         ("modified_zn_stain", "Modified ZN Stain",),
#     )
#
#
# class QuickFISH(FishForm, lmodels.LabTest):
#     _title = "QuickFISH"
#
#     class Meta:
#         proxy = True
#         verbose_name = "QuickFISH"
#
#     RESULT_CHOICES = (
#         ("c_albicans", "C. albicans",),
#         ("c_parapsilosis", "C. parapsilosis",),
#         ("c_glabrata", "C. glabrata",),
#         ("negative", "Negative",),
#     )
#
#
# class GPCStaph(FishForm, lmodels.LabTest):
#     _title = "GPC Staph"
#     class Meta:
#         proxy = True
#         verbose_name = "GPC Staph"
#
#     RESULT_CHOICES = (
#         ("s_aureus", "S. aureus",),
#         ("cns", "CNS",),
#         ("negative", "Negative",),
#     )
#
#
# class GPCStrep(FishForm, lmodels.LabTest):
#     _title = "GPC Strep"
#     class Meta:
#         proxy = True
#         verbose_name = "GPC Strep"
#
#     RESULT_CHOICES = (
#         ("e_faecalis", "E.faecalis",),
#         ("other_enterocci", "Other enterococci",),
#         ("negative", "Negative",),
#     )
#
#
# class GNR(FishForm, lmodels.LabTest):
#     _title = "GNR"
#
#     class Meta:
#         proxy = True
#         verbose_name = "GNR"
#
#     RESULT_CHOICES = (
#         ("e_coli", "E.coli",),
#         ("k_pneumoniae", "K. pneumoniae",),
#         ("p_aeruginosa", "P. aeruginosa",),
#         ("negative", "Negative",),
#     )
#
#
# class OrganismTest(lmodels.LabTest):
#     _title = "Organism"
#
#     class Meta:
#         proxy = True
#         verbose_name = "Organism"
#
#     def get_result_look_up_list(self):
#         return "microbiology_organism_list"
#
#     @classmethod
#     def get_form_template(self, *args, **kwargs):
#         return "lab_tests/forms/sensitive_resistant_form.html"


# class BloodCultureIsolate(
#     lmodels.LabTestCollection,
#     omodels.UpdatesFromDictMixin,
#     omodels.ToDictMixin,
#     omodels.TrackedModel
# ):
#     consistency_token = models.CharField(max_length=8)
#     aerobic = models.BooleanField()
#     blood_culture = models.ForeignKey(BloodCulture, related_name="isolates")
#
#     @classmethod
#     def _get_fieldnames_to_serialize(cls):
#         field_names = super(BloodCultureIsolate, cls)._get_fieldnames_to_serialize()
#         field_names.append("blood_culture_id")
#         return field_names


class FinalDiagnosis(EpisodeSubrecord):
    _icon = 'fa fa-pencil-square'
    _title = "Final Diagnosis"

    source = models.CharField(max_length=255, blank=True)
    contaminant = models.BooleanField(default=False)
    community_related = models.BooleanField(default=False)
    hcai_related = models.BooleanField(verbose_name="HCAI related", default=False)


class ImagingTypes(lookuplists.LookupList): pass


class Imaging(EpisodeSubrecord):
    _icon = 'fa fa-eye'

    date = models.DateField(blank=True, null=True)
    imaging_type = ForeignKeyOrFreeText(ImagingTypes)
    site = models.CharField(max_length=200, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
