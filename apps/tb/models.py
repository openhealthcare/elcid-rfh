"""
Models for tb
"""
from django.db import models as fields
from opal.core.fields import ForeignKeyOrFreeText
from opal.core import lookuplists
from opal import models


class RecreationalDrug(lookuplists.LookupList):
    pass


class SocialHistory(models.EpisodeSubrecord):
    _is_singleton = True
    _title = 'Social History'
    _icon = 'fa fa-clock-o'
    HOMELESSNESS_TYPE_CHOICES = (
        ("Hostel", "Hostel",),
        ("Sofa surfing", "Sofa surfing",),
        ("Street", "Street",),
        ("Other", "Other",),
    )

    HOMELESSNESS_CHOICES = (
        ('Never', 'Never',),
        ('Current', 'Current',),
        ('Past', 'Past'),
    )

    ALCOHOL_CHOICES = (
        ("None", "None",),
        ("Occasional", "Occasional",),
        ("Excess", "Excess",),
        ("Dependent", "Dependent",),
    )

    SMOKING_CHOICES = (
        ("Never", "Never",),
        ("Current", "Current",),
        ("Past", "Past",),
    )

    RECREATIONAL_DRUG_USE = (
        ("Never", "Never",),
        ("Current", "Current",),
        ("Dependent", "Dependent",),
        ("Past", "Past",),
    )

    PRISON_CHOICES = (
        ("Never", "Never",),
        ("Current", "Current",),
        ("Within the last 5 years", "Within the last 5 years",),
        ("Over 5 years ago", "Over 5 years ago",),
    )

    notes = fields.TextField(blank=True, null=True)

    smoking = fields.CharField(
        max_length=250,
        choices=SMOKING_CHOICES,
        blank=True,
        null=True
    )

    drinking = fields.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="Alcohol",
        choices=ALCOHOL_CHOICES
    )
    history_of_alocohol_dependence = fields.BooleanField(
        default=False
    )
    recreational_drug_use = fields.CharField(
        max_length=250,
        choices=RECREATIONAL_DRUG_USE,
        blank=True,
        null=True
    )
    opiate_replacement_therapy = fields.BooleanField(
        default=False,
        verbose_name="on opiate replacement therapy"
    )
    drug_community_worker = fields.CharField(
        verbose_name="Drug/alcohol worker",
        max_length=256,
        blank=True,
        null=True,
    )

    homelessness_type = fields.CharField(
        blank=True,
        null=True,
        choices=HOMELESSNESS_TYPE_CHOICES,
        max_length=256
    )

    homelessness = fields.CharField(
        blank=True,
        null=True,
        choices=HOMELESSNESS_CHOICES,
        max_length=256
    )

    housing_officer = fields.CharField(
        max_length=256,
        blank=True,
        null=True
    )

    recreational_drug_type = ForeignKeyOrFreeText(RecreationalDrug)
    receiving_treatment = fields.BooleanField(default=False)
    prison_history = fields.CharField(
        max_length=250,
        choices=PRISON_CHOICES,
        blank=True,
        null=True
    )
    prison_history_details = fields.TextField(
        default="", blank=True
    )
    probation_officer = fields.CharField(
        max_length=256,
        blank=True,
        null=True
    )

    mental_health_issues = fields.BooleanField(
        default=False
    )

    # if they patient has mental health issues
    # store the Community pysiatric nurse (CPN) or
    # the Community mental health team (CMHT)
    community_nurse = fields.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="CPN/CMHT"
    )


class Nationality(models.PatientSubrecord):
    _is_singleton = True

    immigration_concerns = fields.BooleanField(default=False)
    immigration_details = fields.TextField(blank=True)
    immigration_support_officer = fields.TextField(blank=True)

    arrival_in_the_uk = fields.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name="Year of arrival in the UK"
    )

    class Meta:
        verbose_name = "Nationality & Citizenship"
        verbose_name_plural = "Nationality & Citizenship"


class Employment(models.PatientSubrecord):
    _is_singleton = True

    FINANICAL_STATUS_CHOICES = (
        ("Nil income", "Nil income"),
        ("On benefits", "On benefits",),
        ("Other(SS/NASS)", "Other(SS/NASS)",),
        ("Employed", "Employed",),
    )

    occupation = fields.TextField(blank=True, null=True)
    financial_status = fields.CharField(
        max_length=256,
        choices=FINANICAL_STATUS_CHOICES
    )


class CommuninicationConsiderations(models.PatientSubrecord):
    _is_singleton = True

    class Meta:
        verbose_name = "Communication"
        verbose_name_plural = "Communinication Considerations"

    needs_an_interpreter = fields.BooleanField(
        default=False
    )
    language = fields.CharField(
        max_length=256, blank=True
    )
    sensory_impairment = fields.BooleanField(
        default=False
    )


class AccessConsiderations(models.PatientSubrecord):
    _is_singleton = True

    ACCESS_ASSISTANCE = (
        ("provision", "provision",),
        ("finance", "finance",),
    )

    class Meta:
        verbose_name = "Access & Transport"
        verbose_name_plural = "Access Considerations"

    mobility_problem = fields.BooleanField(
        default=False
    )

    needs_help_with_transport = fields.BooleanField(
        default=False
    )
    access_assistance = fields.CharField(
        blank=True,
        null=True,
        choices=ACCESS_ASSISTANCE,
        max_length=256
    )


class PatientConsultation(models.PatientConsultation):
    pass


class ContactDetails(models.PatientSubrecord):
    _is_singleton = True
    _advanced_searchable = False
    _icon = 'fa fa-phone'
    _title = 'Contact Details'

    # telephone = fields.CharField(blank=True, null=True, max_length=50)
    # email = fields.CharField(blank=True, null=True, max_length=255)
    # address = fields.TextField(blank=True, null=True)
    details = fields.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Contact details"


class NextOfKin(models.PatientSubrecord):
    _icon = 'fa fa-child'
    _advanced_searchable = False
    _title = 'Next Of Kin'

    first_name = fields.CharField(blank=True, null=True, max_length=255)
    surname = fields.CharField(blank=True, null=True, max_length=255)
    details = fields.TextField(blank=True, null=True)


class TBSite(lookuplists.LookupList):
    pass


class TBTreatmentCentre(lookuplists.LookupList):
    pass


class LymphNodeSwellingSiteOptions(lookuplists.LookupList):
    pass


class LymphNodeSwellingSite(models.EpisodeSubrecord):
    site = ForeignKeyOrFreeText(LymphNodeSwellingSiteOptions)


class Treatment(models.Treatment):
    _angular_service = 'TreatmentRecord'
    planned_end_date = fields.DateField(blank=True, null=True)


class TBHistory(models.PatientSubrecord):
    """ Used if the person has clicked that they
        have a personal history of TB in the
        initial assessment form
    """
    _icon = 'fa fa-clock-o'
    _title = "History of TB"
    _is_singleton = True

    TB_TYPES = (
        ("Active", "Active",),
        ("Latent", "Latent",),
        ("Unknown", "Unknown",),
    )

    NONE = "None"
    PREVIOUS_TB_DIAGNOSIS = "Previous TB Diagnosis"
    PREVIOUS_TB_CONTACT = "Previous TB Contact"

    PREVIOUS_CONTACT = (
        (PREVIOUS_TB_DIAGNOSIS, PREVIOUS_TB_DIAGNOSIS,),
        (PREVIOUS_TB_CONTACT, PREVIOUS_TB_CONTACT,),
        (NONE, NONE,),
    )

    _is_singleton = True
    previous_tb_contact = fields.CharField(
        blank=True,
        choices=PREVIOUS_CONTACT,
        default=NONE,
        max_length=100
    )
    how_long_ago_years = fields.IntegerField(
        blank=True, null=True
    )
    how_long_ago_months = fields.IntegerField(
        blank=True, null=True
    )
    how_long_ago_days = fields.IntegerField(
        blank=True, null=True
    )
    how_long_treated_years = fields.IntegerField(
        blank=True, null=True
    )
    how_long_treated_months = fields.IntegerField(
        blank=True, null=True
    )
    how_long_treated_days = fields.IntegerField(
        blank=True, null=True
    )
    tb_type = fields.CharField(
        blank=True,
        null=True,
        choices=TB_TYPES,
        max_length=256,
        verbose_name="TB Type"
    )
    site_of_tb = ForeignKeyOrFreeText(
        TBSite, verbose_name="Site of TB"
    )
    country_treated = ForeignKeyOrFreeText(models.Destination)
    treatment_centre = ForeignKeyOrFreeText(TBTreatmentCentre)
    details = fields.TextField(default="")


class Allergies(models.Allergies):
    pass


class Travel(models.EpisodeSubrecord):
    _icon = 'fa fa-plane'
    _title = "Travel History"

    country = ForeignKeyOrFreeText(models.Destination)
    when = fields.CharField(max_length=255, blank=True)
    duration = fields.CharField(max_length=255, blank=True)
    reason_for_travel = ForeignKeyOrFreeText(models.Travel_reason)


class TBLocation(models.EpisodeSubrecord):
    _is_singleton = True
    sites = fields.ManyToManyField(TBSite, blank=True)

    def to_dict(self, user):
        result = super(TBLocation, self).to_dict(user)
        result["sites"] = list(self.sites.values_list("name", flat=True))
        return result


class BCG(models.PatientSubrecord):
    _icon = 'fa fa-asterisk'
    _title = "BCG"
    _is_singleton = True
    BCG_PERIOD = (
        ('Neonatal', 'Neonatal',),
        ('School', 'School',),
        ('Adult', 'Adult',),
        ('Unsure', 'Unsure',),
        ('None', 'None',)
    )
    bcg_type = fields.CharField(
        max_length=255,
        blank=True,
        choices=BCG_PERIOD,
        verbose_name="BCG"
    )
    bcg_scar = fields.BooleanField(default=False, verbose_name="BCG Scar Seen")
    red_book_documentation_of_bcg_seen = fields.BooleanField(
        default=False, verbose_name="Red Book Documentation Of BCG Given"
    )


class MantouxTest(models.PatientSubrecord):
    MANTOUX_SITES = (
        ("Left Lower Arm", "Left Lower Arm",),
        ("Right Lower Arm", "Right Lower Arm",),
    )
    batch_number = fields.CharField(
        max_length=256, blank=True, default=""
    )
    expiry_date = fields.DateField(blank=True, null=True)
    induration = fields.IntegerField(
        verbose_name="Induration (mm)",
        blank=True,
        null=True
    )
    site = fields.CharField(
        max_length=256, blank=True, default="", choices=MANTOUX_SITES
    )


class TBMeta(models.EpisodeSubrecord):
    _is_singleton = True
    _advanced_searchable = False

    contact_tracing_done = fields.BooleanField(default=False)
    directly_observed_therapy = fields.BooleanField(default=False)
