"""
elCID implementation specific models!
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from opal.utils import AbstractBase, _itersubclasses, camelcase_to_underscore

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

    pid_fields       = (
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

class BloodCulture(EpisodeSubrecord):
    _icon = 'fa fa-crosshairs'
    _title = 'Blood Culture'
    _angular_service = 'BloodCultureRecord'

    lab_number = models.CharField(max_length=255, blank=True)
    date_ordered = models.DateField(null=True, blank=True)
    date_positive = models.DateField(null=True, blank=True)
    source = ForeignKeyOrFreeText(BloodCultureSource)

    @classmethod
    def _get_fieldnames_to_serialize(cls):
        field_names = super(BloodCulture, cls)._get_fieldnames_to_serialize()
        field_names.append("isolates")
        return field_names

    def update_from_dict(self, data, user, **kwargs):
        isolates = data.pop("isolates", [])
        existing = [i["id"] for i in isolates if "id" in i]
        self.isolates.exclude(id__in=existing).delete()
        kwargs.pop("fields", None)
        fields = set(self.__class__._get_fieldnames_to_serialize())
        fields.remove("isolates")
        super(BloodCulture, self).update_from_dict(data, user, fields=fields, **kwargs)

        for isolate in isolates:
            isolate_id = isolate.get("id")

            if isolate_id:
                blood_culture_isolate = self.isolates.get(
                    id=isolate_id
                )
            else:
                blood_culture_isolate = BloodCultureIsolate(
                    blood_culture_id=self.id
                )

            blood_culture_isolate.update_from_dict(isolate, user, **kwargs)

    def get_isolates(self, user):
        return [i.to_dict(user) for i in self.isolates.all()]


class LabTest(omodels.UpdatesFromDictMixin, omodels.ToDictMixin, omodels.TrackedModel):
    consistency_token = models.CharField(max_length=8)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    test_name = models.CharField(max_length=256)
    details = JSONField(blank=True, null=True)
    result = models.CharField(blank=True, null=True, max_length=256)
    sensitive_antibiotics = models.ManyToManyField(
        omodels.Antimicrobial, related_name="test_sensitive"
    )
    resistant_antibiotics = models.ManyToManyField(
        omodels.Antimicrobial, related_name="test_resistant"
    )

    def get_object(self):
        if self.test_name:
            test_class = self.__class__.get_class_from_test_name(
                self.test_name
            )

            if test_class:
                self.__class__ = test_class
        return self

    @classmethod
    def get_class_from_test_name(cls, test_name):
        for test_class in _itersubclasses(cls):
            if test_class.get_api_name() == test_name:
                return test_class

    def save(self, *args, **kwargs):
        if not isinstance(models.Model, AbstractBase):
            self.test_name = self.__class__.get_api_name()

        return super(LabTest, self).save(*args, **kwargs)

    @classmethod
    def get_api_name(cls):
        return camelcase_to_underscore(cls._meta.object_name)

    def update_from_dict(self, data, user, **kwargs):
        fields = set(self.__class__._get_fieldnames_to_serialize())

        # for now lets not save the details
        fields.remove('details')
        fields.remove('sensitive_antibiotics')
        fields.remove('resistant_antibiotics')

        antibiotics = ["sensitive_antibiotics", "resistant_antibiotics"]

        super(LabTest, self).update_from_dict(data, user, fields=fields, **kwargs)

        for k in antibiotics:
            v = data.get(k)

            if v:
                antimicrobials = get_for_lookup_list(omodels.Antimicrobial, v)
                field = getattr(self, k)
                field.clear()
                field.add(*antimicrobials)


class Fish(LabTest):
    pass


class BloodCultureIsolate(omodels.UpdatesFromDictMixin, omodels.ToDictMixin, omodels.TrackedModel):
    consistency_token = models.CharField(max_length=8)
    aerobic = models.BooleanField()
    organism = models.ForeignKey(
        omodels.Microbiology_organism,
        related_name="blood_culture_isolate_organisms",
        null=True,
        blank=True
    )

    microscopy = models.ForeignKey(
        omodels.Microbiology_organism,
        related_name="blood_culture_microscopy_organisms",
        null=True,
        blank=True
    )
    sensitive_antibiotics = models.ManyToManyField(
        omodels.Antimicrobial, related_name="blood_culture_sensitive"
    )
    resistant_antibiotics = models.ManyToManyField(
        omodels.Antimicrobial, related_name="blood_culture_resistant"
    )
    blood_culture = models.ForeignKey(BloodCulture, related_name="isolates")

    @classmethod
    def _get_fieldnames_to_serialize(cls):
        field_names = super(BloodCultureIsolate, cls)._get_fieldnames_to_serialize()
        fk_fields = [
            "blood_culture_id",
            "aerobic",
            "fish",
            "microscopy",
            "organism",
            "sensitive_antibiotics"
        ]
        field_names.extend(fk_fields)
        return field_names

    def get_organism(self, user):
        return self.organism.name if self.organism else None

    def get_fish(self, user):
        return [i.to_dict(user) for i in self.get_tests("fish")]

    def get_microscopy(self, user):
        return self.microscopy.name if self.microscopy else None

    def get_sensitive_antibiotics(self, user):
        return [i.name for i in self.sensitive_antibiotics.all()]

    def get_resistant_antibiotics(self, user):
        return [i.name for i in self.resistant_antibiotics.all()]

    def get_tests(self, test_name):
        ct = ContentType.objects.get_for_model(self.__class__)
        object_id = self.id
        return LabTest.objects.filter(
            content_type=ct, object_id=object_id, test_name=test_name
        )

    def save_tests(self, tests, user):
        for test in tests:
            ct = ContentType.objects.get_for_model(self.__class__)
            object_id = self.id
            if "id" in test:
                test_obj = LabTest.objects.get(id=test["id"])
            else:
                test_obj = LabTest()
                test_obj.content_type = ct
                test_obj.object_id = object_id
            test_obj.update_from_dict(test, user)

    def update_from_dict(self, data, user, **kwargs):
        self.aerobic = data["aerobic"]
        organisms = ["microscopy", "organism"]

        for k in organisms:
            v = data.get(k)
            organism_models = get_for_lookup_list(omodels.Microbiology_organism, [v])
            organism = None

            if organism_models:
                organism = organism_models[0]
            setattr(self, k, organism)

        self.save()

        antibiotics = ["sensitive_antibiotics", "resistant_antibiotics"]

        for k in antibiotics:
            v = data.get(k)

            if v:
                antimicrobials = get_for_lookup_list(omodels.Antimicrobial, v)
                field = getattr(self, k)
                field.clear()
                field.add(*antimicrobials)

        fishes = data.get("fish", [])

        for fish in fishes:
            fish["test_name"] = "fish"

        self.save_tests(fishes, user)

        fields = {
            "created_by", "updated_by", "updated", "created", "consistency_token"
        }
        additional_data = {i: v for i, v in data.iteritems() if i in fields}
        super(BloodCultureIsolate, self).update_from_dict(
            additional_data, user, fields=fields, **kwargs
        )


class FinalDiagnosis(EpisodeSubrecord):
    _icon = 'fa fa-eye'
    _title = "Final Diagnosis"

    source = models.CharField(max_length=255, blank=True)
    contaminant = models.BooleanField(default=False)
    community_related = models.BooleanField(default=False)
    hcai_related = models.BooleanField(default=False)


class ImagingTypes(lookuplists.LookupList): pass


class Imaging(EpisodeSubrecord):
    _icon = 'fa fa-eye'

    date = models.DateField(blank=True, null=True)
    imaging_type = ForeignKeyOrFreeText(ImagingTypes)
    site = models.CharField(max_length=200, blank=True, null=True)
    details = models.TextField(blank=True, null=True)


@receiver(post_save, sender=Episode)
def get_information_from_gloss(sender, **kwargs):
    from elcid import gloss_api

    episode = kwargs.pop("instance")
    created = kwargs.pop("created")
    if created and settings.GLOSS_ENABLED:
        hospital_number = episode.patient.demographics_set.first().hospital_number
        gloss_api.subscribe(hospital_number)
        gloss_api.patient_query(hospital_number, episode=episode)
