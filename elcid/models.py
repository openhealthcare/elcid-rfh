"""
elCID implementation specific models!
"""
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.contrib.contenttypes.models import ContentType
from lab import models as lmodels


import opal.models as omodels

from opal.models import (
    EpisodeSubrecord, PatientSubrecord, ExternallySourcedModel
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


class ContactDetails(PatientSubrecord):
    _is_singleton = True
    _advanced_searchable = False
    _icon = 'fa fa-phone'

    address_line1 = models.CharField(
        "Address line 1", max_length=45, blank=True, null=True
    )
    address_line2 = models.CharField(
        "Address line 2", max_length=45, blank=True, null=True
    )
    city = models.CharField(
        max_length=50, blank=True, null=True
    )
    county = models.CharField(
        "County", max_length=40, blank=True, null=True
    )
    post_code = models.CharField(
        "Post Code", max_length=10, blank=True, null=True
    )
    tel1 = models.CharField(blank=True, null=True, max_length=50)
    tel2 = models.CharField(blank=True, null=True, max_length=50)

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
    bed = models.CharField(max_length=255, blank=True, null=True)

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


class HL7Result(lmodels.ReadOnlyLabTest):
    class Meta:
        verbose_name = "HL7 Result"

    @classmethod
    def get_api_name(cls):
        return "hl7_result"

    def to_dict(self, user):
        """
            we don't serialise a subrecord during episode
            serialisation
        """
        return {
            "lab_test_type": self.__class__.get_display_name(),
            "id": self.id
        }

    def dict_for_view(self, user):
        """
            we serialise the usual way but not via the episode
            serialisation
        """
        return super(HL7Result, self).to_dict(user)

    def update_from_dict(self, data, *args, **kwargs):
        populated = (
            i for i in data.keys() if i != "lab_test_type" and i != "id"
        )
        if not any(populated):
            return

        if "id" not in data:
            if 'patient_id' in data:
                self.patient = omodels.Patient.objects.get(id=data['patient_id'])

            if "external_identifier" not in data:
                raise ValueError(
                    "an external identifier is required in {}".format(data)
                )
            if "external_identifier" in data and data["external_identifier"]:
                existing = self.__class__.objects.filter(
                    patient=self.patient,
                    external_identifier=data["external_identifier"],
                ).first()

                if existing:
                    data["id"] = existing.id
            super(HL7Result, self).update_from_dict(data, *args, **kwargs)

    @classmethod
    def get_relevant_tests(self, patient):
        relevent_tests = [
            "C REACTIVE PROTEIN",
            "FULL BLOOD COUNT",
            "UREA AND ELECTROLYTES",
            "LIVER FUNCTION",
            "LIVER PROFILE",
            "GENTAMICIN LEVEL",
            "CLOTTING SCREEN"
        ]
        six_months_ago = datetime.date.today() - datetime.timedelta(6*30)
        qs = HL7Result.objects.filter(
            patient=patient,
            datetime_ordered__gt=six_months_ago
        ).order_by("datetime_ordered")
        return [i for i in qs if i.extras.get("profile_description") in relevent_tests]


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


class Consultant(lookuplists.LookupList):
    pass


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
    date = models.DateField(blank=True, null=True)


class BloodCultureSource(lookuplists.LookupList):
    pass


class RfhObservation(object):
    def __unicode__(self):
        return "{} for {}".format(
            self.observation_type, self.lab_test
        )


class SourceObservation(lmodels.Observation, RfhObservation):
    class Meta:
        proxy = True
        auto_created = True

    lookup_list = BloodCultureSource


class BloodCultureMixin(object):
    # note the isolate field isn't an official reference, its just
    # used to group isolates on the front end (at present)
    _extras = ['isolate', 'aerobic', 'source', 'lab_number']
    source = SourceObservation()

    @classmethod
    def get_record(cls):
        return "lab/records/blood_culture.html"

    def update_from_dict(self, data, *args, **kwargs):
        result = data.get("result", None)
        if "date_ordered" in data:
            date_ordered = data.pop("date_ordered")
            if isinstance(date_ordered, str):
                date_ordered = date_ordered.strip()
                data["datetime_ordered"] = datetime.combine(
                    date_ordered, datetime.min.time()
                )

        if result:
            result = result.get("result", None)

        if result:
            result = result.strip()

        if not result or result == 'Not Done':
            if self.id:
                self.delete()
        else:
            super(BloodCultureMixin, self).update_from_dict(data, *args, **kwargs)


class GramStainResult(lmodels.Observation, RfhObservation):
    class Meta:
        proxy = True
        auto_created = True

    RESULT_CHOICES = (
        ("Yeast", "Yeast"),
        ("Gram +ve Cocci Cluster", "Gram +ve Cocci Cluster"),
        ("Gram +ve Cocci Chains", "Gram +ve Cocci Chains"),
        ("Gram -ve Rods", "Gram -ve Rods"),
        ("Not Done", "Not Done"),
    )


class GramStain(BloodCultureMixin, lmodels.LabTest):
    _title="Gram Stain"
    result = GramStainResult()


class QuickFishResult(lmodels.Observation, RfhObservation):
    class Meta:
        proxy = True
        auto_created = True

    RESULT_CHOICES = (
        ("C. albicans", "C. albicans"),
        ("C. parapsilosis", "C. parapsilosis"),
        ("C. glabrata", "C. glabrata"),
        ("Negative", "Negative"),
        ("Not Done", "Not Done"),
    )


class QuickFISH(BloodCultureMixin, lmodels.LabTest):
    _title = "QuickFISH"
    result = QuickFishResult()


class GPCStaphResult(lmodels.Observation, RfhObservation):
    class Meta:
        proxy = True
        auto_created = True

    RESULT_CHOICES = (
        ("S. aureus", "S. aureus"),
        ("CNS", "CNS"),
        ("Negative", "Negative"),
        ("Not Done", "Not Done"),
    )


class GPCStaph(BloodCultureMixin, lmodels.LabTest):
    result = GPCStaphResult()
    _title = 'GPC Staph'


class GPCStrepResult(lmodels.Observation, RfhObservation):
    class Meta:
        proxy = True
        auto_created = True

    RESULT_CHOICES = (
        ("E.faecalis", "E.faecalis"),
        ("Other enterococci", "Other enterococci"),
        ("Negative", "Negative"),
        ("Not Done", "Not Done"),
    )


class GPCStrep(BloodCultureMixin, lmodels.LabTest):
    result = GPCStrepResult()
    _title = "GPC Strep"


class GNRResult(lmodels.Observation, RfhObservation):
    class Meta:
        proxy = True
        auto_created = True

    RESULT_CHOICES = (
        ("E.faecalis", "E.coli"),
        ("K. pneumoniae", "K. pneumoniae"),
        ("P. aeruginosa", "P. aeruginosa"),
        ("Negative", "Negative"),
        ("Not Done", "Not Done"),
    )


class GNR(BloodCultureMixin, lmodels.LabTest):
    _title = 'GNR'
    result = GNRResult()


class Organism(lmodels.Observation, RfhObservation):
    class Meta:
        proxy = True

    lookup_list = omodels.Microbiology_organism


class BloodCultureOrganism(BloodCultureMixin, lmodels.LabTest):
    _title = 'Organism'
    result = Organism()


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


class PositiveBloodCultureHistory(PatientSubrecord):
    when = models.DateTimeField(default=datetime.datetime.now)

    @classmethod
    def _get_field_default(cls, name):
        # this should not be necessary...
        return None


# method for updating
@receiver(post_save, sender=omodels.Tagging)
def record_positive_blood_culture(sender, instance, **kwargs):
    from elcid.patient_lists import Bacteraemia

    if instance.value == Bacteraemia.tag:
        pbch, _ = PositiveBloodCultureHistory.objects.get_or_create(
            patient_id=instance.episode.patient.id
        )
        pbch.when = datetime.datetime.now()
        pbch.save()
