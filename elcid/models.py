"""
elCID implementation specific models!
"""
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from opal.utils import camelcase_to_underscore
import opal.models as omodels
from obs import models as obs_models

from opal.models import (
    EpisodeSubrecord, PatientSubrecord, ExternallySourcedModel, Patient
)
from opal.core.fields import ForeignKeyOrFreeText, enum
from opal.core import lookuplists
from elcid.episode_categories import InfectionService


def get_for_lookup_list(model, values):
    ct = ContentType.objects.get_for_model(model)
    return model.objects.filter(
        models.Q(name__in=values) |
        models.Q(synonyms__name__in=values, synonyms__content_type=ct)
    )


class MergedMRN(models.Model):
    """
    Represents each time this patient has had a duplicate MRN merged.

    e.g. if MRN 77456 was merged into patient 123
    Patient 123 would have a patient merge object with MRN 77456
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    mrn = models.CharField(max_length=256, unique=True, db_index=True)
    merge_comments = models.TextField(blank=True, null=True, default="")
    our_merge_datetime = models.DateTimeField(blank=True, null=True)


class PreviousMRN(models.Model):
    """
    A mixin for subrecords to maintain an audit trail for occasions
    when an upstream MRN merge occurs and the merged MRN has elCID entries.

    `previous_mrn` is the MRN in use at the time that this subrecord instance
    was last created/edited with if that MRN is different from the current
    value of `Demographics.hospital_number` attached to this instance.
    """
    previous_mrn = models.CharField(blank=True, null=True, max_length=256)

    class Meta:
        abstract = True



class Demographics(PreviousMRN, omodels.Demographics, ExternallySourcedModel):
    _is_singleton = True
    _icon = 'fa fa-user'

    pid_fields = (
        'hospital_number', 'nhs_number', 'surname', 'first_name',
        'middle_name', 'post_code',
    )
    religion = models.CharField(blank=True, null=True, max_length=100)
    main_language = models.CharField(blank=True, null=True, max_length=100)
    nationality = models.CharField(blank=True, null=True, max_length=100)

    @property
    def age(self):
        if self.date_of_birth:
            return datetime.date.today().year - self.date_of_birth.year

    def save(self, *args, **kwargs):
        """
        Remove any zero prefix on the hospital number
        """
        self.hospital_number = self.hospital_number.lstrip('0')
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Demographics"


class ContactInformation(PatientSubrecord, ExternallySourcedModel):
    """
    Address and contact details from the Patient_Masterfile upstream table
    """
    _is_singleton = True
    _icon = 'fa fa-phone'
    _exclude_from_extract = True

    address_line_1 = models.CharField(blank=True, null=True, max_length=100)
    address_line_2 = models.CharField(blank=True, null=True, max_length=100)
    address_line_3 = models.CharField(blank=True, null=True, max_length=100)
    address_line_4 = models.CharField(blank=True, null=True, max_length=100)
    postcode = models.CharField(blank=True, null=True, max_length=20)
    home_telephone = models.CharField(blank=True, null=True, max_length=100)
    work_telephone = models.CharField(blank=True, null=True, max_length=100)
    mobile_telephone = models.CharField(blank=True, null=True, max_length=100)
    email = models.CharField(blank=True, null=True, max_length=100)


class NextOfKinDetails(PatientSubrecord, ExternallySourcedModel):
    """
    Next of kin details from the Patient_Masterfile upstream table
    """
    _is_singleton = True
    _icon = 'fa fa-users'
    _exclude_from_extract = True

    nok_type = models.CharField(blank=True, null=True, max_length=100)
    surname = models.CharField(blank=True, null=True, max_length=100)
    forename_1  = models.CharField(blank=True, null=True, max_length=100)
    forename_2  = models.CharField(blank=True, null=True, max_length=100)
    relationship = models.CharField(blank=True, null=True, max_length=100)
    address_1 = models.CharField(blank=True, null=True, max_length=100)
    address_2 = models.CharField(blank=True, null=True, max_length=100)
    address_3 = models.CharField(blank=True, null=True, max_length=100)
    address_4 = models.CharField(blank=True, null=True, max_length=100)
    postcode = models.CharField(blank=True, null=True, max_length=20)
    work_telephone = models.CharField(blank=True, null=True, max_length=100)
    home_telephone = models.CharField(blank=True, null=True, max_length=100)

    class Meta:
        verbose_name = "Next Of Kin"


class GPDetails(PatientSubrecord, ExternallySourcedModel):
    """
    GP details from the Patient_Masterfile upstream table
    """

    _is_singleton = True
    _icon = 'fa fa-user-circle-o'
    _exclude_from_extract = True

    crs_gp_masterfile_id = models.IntegerField(blank=True, null=True)
    national_code = models.CharField(blank=True, null=True, max_length=20)
    practice_code = models.CharField(blank=True, null=True, max_length=20)
    title = models.CharField(blank=True, null=True, max_length=100)
    initials = models.CharField(blank=True, null=True, max_length=100)
    surname = models.CharField(blank=True, null=True, max_length=100)
    address_1 = models.CharField(blank=True, null=True, max_length=100)
    address_2 = models.CharField(blank=True, null=True, max_length=100)
    address_3 = models.CharField(blank=True, null=True, max_length=100)
    address_4 = models.CharField(blank=True, null=True, max_length=100)
    postcode = models.CharField(blank=True, null=True, max_length=20)
    telephone = models.CharField(blank=True, null=True, max_length=100)

    class Meta:
        verbose_name = "GP"


class MasterFileMeta(models.Model):
    """
    Meta data about the Patient_Masterfile upstream table
    """
    patient = models.ForeignKey(omodels.Patient, on_delete=models.CASCADE)
    insert_date = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)
    merged = models.CharField(blank=True, null=True, max_length=20)
    merge_comments = models.TextField(blank=True, null=True)
    active_inactive = models.CharField(blank=True, null=True, max_length=20)

    @classmethod
    def get_api_name(cls):
        return camelcase_to_underscore(cls._meta.object_name)


class DuplicatePatient(PatientSubrecord):
    _no_admin = True
    _icon = 'fa fa-clone'
    _advanced_searchable = False
    reviewed = models.BooleanField(default=False)
    merged = models.BooleanField(default=False)

    def icon(self):
        return self._icon


class Provenance(lookuplists.LookupList):
    pass


class MicrobiologyOrganism(lookuplists.LookupList):
    pass


class LineType(lookuplists.LookupList):
    pass


class LineSite(lookuplists.LookupList):
    pass


class LineComplication(lookuplists.LookupList):
    pass


class LineRemovalReason(lookuplists.LookupList):
    pass


class Location(PreviousMRN, EpisodeSubrecord):
    _is_singleton = True
    _icon = 'fa fa-map-marker'

    provenance = ForeignKeyOrFreeText(Provenance)
    hospital   = ForeignKeyOrFreeText(omodels.Hospital)
    ward       = ForeignKeyOrFreeText(omodels.Ward)
    bed        = models.CharField(max_length=255, blank=True, null=True)
    consultant = models.CharField(max_length=255, blank=True, null=True)
    unit       = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        try:
            demographics = self.episode.patient.demographics_set.get()
            return u'Location for {0}({1}) {2} {3} {4}'.format(
                demographics.name,
                demographics.hospital_number,
                self.hospital,
                self.ward,
                self.bed
            )
        except:
            return 'demographics'


class InfectionSource(lookuplists.LookupList):
    pass


class Infection(PreviousMRN, EpisodeSubrecord):
    """
    This model is deprecated
    """
    _icon = 'fa fa-eyedropper'
    # this needs to be fixed
    source = ForeignKeyOrFreeText(InfectionSource)
    site = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Infection Related Issues"


class Procedure(PreviousMRN, EpisodeSubrecord):
    _icon = 'fa fa-sitemap'

    STAGE_CHOICES = enum(
        'Partial',
        '1st stage',
        'Re-do 1st stage',
        '2nd stage'
    )

    OPERATION_CHOICES = enum(
        'Prmary',
        'Revision',
        'Decompression',
        'Fixation'
    )
    SITE_CHOICES = enum(
        'THR',
        'TKR',
        'TSR',
        'TER',
        'TAR'

    )

    date      = models.DateField(blank=True, null=True)
    hospital  = ForeignKeyOrFreeText(omodels.Hospital)
    stage     = models.CharField(blank=True, null=True, max_length=100, choices=STAGE_CHOICES)
    operation = models.CharField(blank=True, null=True, max_length=100, choices=OPERATION_CHOICES)
    side      = models.CharField(blank=True, null=True, max_length=100, choices=enum('R', 'L'))
    site      = models.CharField(blank=True, null=True, max_length=100, choices=SITE_CHOICES)
    findings  = models.TextField(blank=True, null=True)
    details   = models.TextField(blank=True, null=True)


    class Meta:
        verbose_name = "Operation / Procedures"


class PrimaryDiagnosisCondition(lookuplists.LookupList): pass


class PrimaryDiagnosis(PreviousMRN, EpisodeSubrecord):
    """
    This is the confirmed primary diagnosisa
    """
    _is_singleton = True
    _icon = 'fa fa-eye'

    condition = ForeignKeyOrFreeText(PrimaryDiagnosisCondition)
    confirmed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Primary Diagnosis'
        verbose_name_plural = "Primary Diagnoses"


class Consultant(lookuplists.LookupList):
    pass


class Diagnosis(PreviousMRN, omodels.Diagnosis):
    category = models.CharField(max_length=256, blank=True, null=True)

    PRIMARY = "primary"


class Iv_stop(lookuplists.LookupList):
    class Meta:
        verbose_name = "IV stop"


class Drug_delivered(lookuplists.LookupList):
    class Meta:
        verbose_name_plural = "Drugs delivered"


class Antimicrobial(PreviousMRN, EpisodeSubrecord):
    _sort = 'start_date'
    _icon = 'fa fa-flask'
    _modal = 'lg'

    EMPIRIC = "Empiric"
    TARGETTED = "Targeted"
    PREEMPTIVE = "Pre-emptive"

    TREATMENT_REASON = enum(EMPIRIC, TARGETTED, PREEMPTIVE)

    class Meta:
        verbose_name = "Anti-Infectives"

    drug          = ForeignKeyOrFreeText(omodels.Antimicrobial)
    dose          = models.CharField(max_length=255, blank=True)
    route         = ForeignKeyOrFreeText(omodels.Antimicrobial_route)
    start_date    = models.DateField(null=True, blank=True)
    end_date      = models.DateField(null=True, blank=True)
    delivered_by  = ForeignKeyOrFreeText(Drug_delivered)
    reason_for_stopping = ForeignKeyOrFreeText(Iv_stop)
    treatment_reason = models.CharField(
        max_length=256, blank=True, null=True, choices=TREATMENT_REASON
    )
    indication = models.CharField(
        max_length=256, blank=True, null=True
    )
    adverse_event = ForeignKeyOrFreeText(omodels.Antimicrobial_adverse_event)
    comments      = models.TextField(blank=True, null=True)
    frequency     = ForeignKeyOrFreeText(omodels.Antimicrobial_frequency)
    no_antimicrobials = models.NullBooleanField(
        default=False, verbose_name="No anti-infectives"
    )

    @classmethod
    def get_display_name(klass):
        # TODO: Yes I know, do this via Meta, but for now no migrations
        # and the panel uses this method...
        return "Anti-infectives"

class RenalFunction(lookuplists.LookupList):
    pass


class LiverFunction(lookuplists.LookupList):
    pass


class MicrobiologyInput(PreviousMRN, EpisodeSubrecord):
    _sort = 'when'
    _icon = 'fa fa-comments'
    _modal = 'lg'
    _list_limit = 3
    ICU_REASON_FOR_INTERACTION = "ICU round"
    ICN_WARD_REVIEW_REASON_FOR_INTERACTION = "ICN Ward Review"
    ANTIFUNGAL_STEWARDSHIP_ROUND = "Antifungal stewardship ward round"

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
    sent_upstream = models.BooleanField(default=False)

    def to_dict(self, *args, **kwargs):
        result = super().to_dict(*args, **kwargs)
        # if MicroInputICURoundRelation.objects.filter(microbiology_input_id=self.id).exists():
        #     result["micro_input_icu_round_relation"] = self.microinputicuroundrelation.to_dict(*args, **kwargs)
        # else:
        #     result["micro_input_icu_round_relation"] = MicroInputICURoundRelation().to_dict()
        return result

    def update_from_dict(self, data, *args, **kwargs):
        micro_input_icu_round_relation = data.pop("micro_input_icu_round_relation", {})
        result = super().update_from_dict(data, *args, **kwargs)

        # if self.reason_for_interaction == self.ICU_REASON_FOR_INTERACTION:
        #     icu_round, _ = MicroInputICURoundRelation.objects.get_or_create(
        #         microbiology_input_id=self.id
        #     )
        #     icu_round.update_from_dict(
        #         self.episode, data.get("when"), micro_input_icu_round_relation, *args, **kwargs
        #     )
        #     return result
        # else:
        #     micro_input = MicroInputICURoundRelation.objects.filter(
        #         microbiology_input_id=self.id
        #     ).first()
        #     if micro_input:
        #         micro_input.delete_self()
        return result

    def delete(self):
        micro_input = MicroInputICURoundRelation.objects.filter(
            microbiology_input_id=self.id
        ).first()
        if micro_input:
            micro_input.delete_self()

        super().delete()

    class Meta:
        verbose_name = "Clinical Advice"
        verbose_name_plural = "Clinical Advice"

# method for updating
@receiver(post_save, sender=MicrobiologyInput)
def update_chronic_antifungal_reason_for_interaction(
    sender, instance, **kwargs
):
    asr = MicrobiologyInput.ANTIFUNGAL_STEWARDSHIP_ROUND
    if instance.reason_for_interaction == asr:
        instance.episode.patient.chronicantifungal_set.create(
            reason=ChronicAntifungal.REASON_TO_INTERACTION
        )


class Line(PreviousMRN, EpisodeSubrecord):
    _sort = 'insertion_datetime'
    _icon = 'fa fa-bolt'

    line_type = ForeignKeyOrFreeText(LineType)
    site = ForeignKeyOrFreeText(LineSite)
    insertion_datetime = models.DateTimeField(blank=True, null=True)
    inserted_by = models.CharField(max_length=255, blank=True, null=True)
    external_length = models.CharField(max_length=255, blank=True, null=True)
    removal_datetime = models.DateTimeField(blank=True, null=True)
    complications = ForeignKeyOrFreeText(LineComplication)
    removal_reason = ForeignKeyOrFreeText(LineRemovalReason)
    special_instructions = models.TextField()
    button_hole = models.NullBooleanField()
    tunnelled_or_temp = models.CharField(max_length=200, blank=True, null=True)
    fistula = models.NullBooleanField(blank=True, null=True)
    graft = models.NullBooleanField(blank=True, null=True)


class BloodCultureSource(lookuplists.LookupList):
    pass


class ImagingTypes(lookuplists.LookupList):
    pass


class Imaging(PreviousMRN, EpisodeSubrecord):
    _icon = 'fa fa-eye'

    date         = models.DateField(blank=True, null=True)
    imaging_type = ForeignKeyOrFreeText(ImagingTypes)
    site         = models.CharField(max_length=200, blank=True, null=True)
    hospital     = ForeignKeyOrFreeText(omodels.Hospital)
    details      = models.TextField(blank=True, null=True)


class ReferralReason(lookuplists.LookupList):
    pass


class ReferralRoute(PreviousMRN, omodels.EpisodeSubrecord):
    _icon = 'fa fa-level-up'
    _is_singleton = True

    date_of_referral = models.DateField(null=True, blank=True)

    referral_type = ForeignKeyOrFreeText(omodels.ReferralType)

    referral_reason = ForeignKeyOrFreeText(ReferralReason)

    details = models.TextField()

    class Meta:
        verbose_name = "Referral Route"


class SymptomComplex(PreviousMRN, omodels.SymptomComplex):
    class Meta:
        verbose_name = "Presenting Symptoms"


class PastMedicalHistory(PreviousMRN, omodels.PastMedicalHistory):
    pass


class GP(PreviousMRN, omodels.PatientSubrecord):
    name = models.CharField(
        max_length=256
    )
    contact_details = models.TextField()


class BloodCultureSet(PreviousMRN, omodels.PatientSubrecord):
    _icon = "fa fa-crosshairs"

    date_ordered = models.DateField(blank=True, null=True)
    source = ForeignKeyOrFreeText(BloodCultureSource)
    lab_number = models.CharField(blank=True, null=True, max_length=256)
    contaminant = models.BooleanField(default=False)
    community = models.BooleanField(default=False, verbose_name='Community Related')
    hcai = models.BooleanField(default=False, verbose_name='HCAI related')

    class Meta:
        verbose_name = "Blood Cultures"

    @classmethod
    def _get_fieldnames_to_serialize(cls, *args, **kwargs):
        field_names = super()._get_fieldnames_to_serialize(*args, **kwargs)
        field_names.append("isolates")
        return field_names

    def get_isolates(self, user, *args, **kwargs):
        return [
            i.to_dict(user) for i in self.isolates.all()
        ]

    def set_isolates(self, *args, **kwargs):
        pass


class GramStainOutcome(lookuplists.LookupList):
    def __str__(self):
        return self.name


class QuickFishOutcome(lookuplists.LookupList):
    def __str__(self):
        return self.name


class GPCStaphOutcome(lookuplists.LookupList):
    def __str__(self):
        return self.name


class GPCStrepOutcome(lookuplists.LookupList):
    def __str__(self):
        return self.name


class GNROutcome(lookuplists.LookupList):
    def __str__(self):
        return self.name


class PatientRiskFactor(lookuplists.LookupList):
    pass


class RiskFactor(PreviousMRN, omodels.PatientSubrecord):
    _icon = 'fa fa-exclamation-triangle'

    risk_factor = ForeignKeyOrFreeText(PatientRiskFactor)
    date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = "Risk Factors"


class BloodCultureIsolate(
    omodels.UpdatesFromDictMixin,
    omodels.ToDictMixin,
    omodels.TrackedModel,
    models.Model
):
    AEROBIC = "Aerobic"
    ANAEROBIC = "Anaerobic"

    AEROBIC_OR_ANAEROBIC = (
        (AEROBIC, AEROBIC,),
        (ANAEROBIC, ANAEROBIC,),
    )

    consistency_token = models.CharField(max_length=8)
    aerobic_or_anaerobic = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        choices=AEROBIC_OR_ANAEROBIC,
        verbose_name="Blood culture bottle type"
    )
    date_positive = models.DateField(blank=True, null=True)
    blood_culture_set = models.ForeignKey(
        "BloodCultureSet",
        on_delete=models.CASCADE,
        related_name="isolates"
    )
    gram_stain = ForeignKeyOrFreeText(GramStainOutcome)
    quick_fish = ForeignKeyOrFreeText(
        QuickFishOutcome, verbose_name="Candida Quick FiSH"
    )
    gpc_staph = ForeignKeyOrFreeText(GPCStaphOutcome, verbose_name="Staph Quick FiSH")
    gpc_strep = ForeignKeyOrFreeText(GPCStrepOutcome, verbose_name="Strep Quick FiSH")
    sepsityper_organism = ForeignKeyOrFreeText(
        MicrobiologyOrganism, related_name="sepsityper_organism"
    )
    organism = ForeignKeyOrFreeText(MicrobiologyOrganism)
    sensitivities = models.ManyToManyField(
        omodels.Antimicrobial, blank=True, related_name="sensitive_isolates"
    )
    resistance = models.ManyToManyField(
        omodels.Antimicrobial, blank=True, related_name="resistant_isolates"
    )
    notes = models.TextField(blank=True)

    @classmethod
    def get_api_name(cls):
        return camelcase_to_underscore(cls._meta.object_name)


class ChronicAntifungal(models.Model):
    DISPENSARY_REPORT = "Dispensary report"
    REASON_TO_INTERACTION = "Reason for interaction"

    REASONS = (
        (DISPENSARY_REPORT, DISPENSARY_REPORT,),
        (REASON_TO_INTERACTION, REASON_TO_INTERACTION,),
    )
    patient = models.ForeignKey(omodels.Patient, on_delete=models.CASCADE)
    updated_dt = models.DateTimeField(auto_now=True)
    reason = models.TextField(
        choices=REASONS, blank=True, null=True
    )

    @classmethod
    def antifungal_episodes(cls):
        # patients should stay on the list for four weeks
        today = datetime.date.today()
        active_from_date = timezone.make_aware(
            datetime.datetime(
                today.year, today.month, today.day, 0, 0
            )
        ) - datetime.timedelta(28)
        return omodels.Episode.objects.filter(
            patient__chronicantifungal__updated_dt__gte=active_from_date
        ).filter(
            category_name=InfectionService.display_name
        ).distinct()


class InotropicDrug(lookuplists.LookupList):
    pass


class Vasopressor(lookuplists.LookupList):
    pass


class ICURound(PreviousMRN, EpisodeSubrecord):
    NIV       = 'NIV'
    INTUBATED = "Intubated"

    VENTILATION_TYPES = enum(NIV, INTUBATED)

    when = models.DateTimeField(
        blank=True, null=True
    )
    ventilation_type = models.CharField(
        max_length=200, blank=True, null=True, choices=VENTILATION_TYPES
    )
    fio2 = models.CharField(
        max_length=20,
        blank=True, null=True, verbose_name="FiO₂"
    )
    inotrope         = ForeignKeyOrFreeText(InotropicDrug)
    inotrope_dose    = models.CharField(max_length=200, blank=True, null=True)
    vasopressor      = ForeignKeyOrFreeText(Vasopressor)
    vasopressor_dose = models.CharField(max_length=200, blank=True, null=True)
    meld_score = models.FloatField(
        blank=True, null=True, verbose_name="MELD score"
    )
    sofa_score = models.FloatField(
        blank=True, null=True, verbose_name="SOFA score"
    )

    class Meta:
        verbose_name = 'ICU Round'


class MicroInputICURoundRelation(models.Model):
    """
    A model that is used when reason for interaction
    is ICU round
    """
    microbiology_input = models.OneToOneField(
        MicrobiologyInput, blank=True, null=True, on_delete=models.SET_NULL
    )
    observation = models.OneToOneField(
        obs_models.Observation, blank=True, null=True, on_delete=models.SET_NULL
    )
    icu_round = models.OneToOneField(
        ICURound,
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    def update_from_dict(self, episode, when, data, *args, **kwargs):
        if self.observation_id:
            observation = self.observation
        else:
            observation = obs_models.Observation(
                episode=episode
            )
        data["observation"]["datetime"] = when
        observation.update_from_dict(data["observation"], *args, **kwargs)
        self.observation_id = observation.id

        if self.icu_round_id:
            icu_round = self.icu_round
        else:
            icu_round = ICURound(
                episode=episode
            )

        data["icu_round"]["when"] = when
        icu_round.update_from_dict(data["icu_round"], *args, **kwargs)
        self.icu_round_id = icu_round.id
        self.save()

    def to_dict(self, *args, **kwargs):
        result = {}
        if self.observation:
            result["observation"] = self.observation.to_dict(*args, **kwargs)
        else:
            result["observation"] = {}

        if self.icu_round:
            result["icu_round"] = self.icu_round.to_dict(*args, **kwargs)
        else:
            result["icu_round"]= {}
        return result

    def delete_self(self):
        if self.observation_id:
            self.observation.delete()
        if self.icu_round_id:
            self.icu_round.delete()
        self.delete()


class InfectionServiceNote(PreviousMRN, EpisodeSubrecord):
    _is_singleton = True
    _icon = 'fa fa-sticky-note'

    text = models.CharField(max_length=200, blank=True, null=True)
