"""
Utility module for blood cultures
"""
from opal.models import Episode

def most_recent_positive(episode_dict):
    """
    Return the most recent +ve culture or None.

    Primarially used as a utility funciton in the Blood Culuture
    for sort and display.
    """
    from elcid.models import BloodCultureSet

    episode = Episode.objects.get(pk=episode_dict['id'])

    most_recent = None
    patient = episode.patient
    cultures = BloodCultureSet.objects.filter(patient=patient)
    for culture in cultures:
        isolates = culture.isolates.all()
        for isolate in isolates:
            if isolate.date_positive:
                if most_recent is None:
                    most_recent = isolate.date_positive
                    continue
                else:
                    if most_recent < isolate.date_positive:
                        most_recent = isolate.date_positive
    return most_recent

def has_labno(culture):
    """
    Validator to check if this Culture has a lab number
    """
    msg = "This patient has a blood culture entered with no \
    lab number entered. Please enter a lab number or remove \
    the culture entry."

    if culture.lab_number:
        return True, None
    return False, msg

def has_date_ordered(culture):
    """
    Validator to check if this culture has a date ordered
    """
    msg = "This patient has a blood culture entered with no \
    date ordered entered. Please enter the date ordered or \
    remove the culture entry."
    if culture.date_ordered:
        return True, None
    return False, msg

def has_source(culture):
    """
    Validator to ensure a source has been entered
    """
    lab_number = culture.lab_number

    msg = f"{lab_number}: This patient has a blood culture entered with no \
    source entered. Please enter the source or remove \
    the culture entry."

    if culture.source:
        return True, None
    return False, msg


def has_category(culture):
    """
    Validator to check if this culture has an appropriate
    level of categorisation (One of 3X descriptive fields)
    """
    lab_number = culture.lab_number

    msg = f"{lab_number}: This patient has a blood culture \
    entered without categorisation as one of Contaminant, \
    Community Related or HCAI related. Please mark culture \
    {lab_number} as one of the above."

    bools = culture.contaminant, culture.community, culture.hcai
    if any(bools):
        return True, None
    return False, msg


def has_bottle_type(culture, isolate):
    """
    Validator to check if this isolate has the bottle type recorded.
    """
    lab_number = culture.lab_number

    msg = f"{lab_number}: This patient has an ambiguous isolate \
    entered. Please record whether the bottle was aerobic or anaerobioc \
    for all isolates in {lab_number}."

    if isolate.aerobic_or_anaerobic:
        return True, None
    return False, msg

def has_organism(culture, isolate):
    """
    Validator to check if this isolate has an organism recorded.
    """
    lab_number = culture.lab_number

    msg = f"{lab_number}: This patient has an isolate \
    entered without an organism recored. Please add the \
    organism to all isolates in {lab_number}."

    if isolate.organism:
        return True, None
    return False, msg

def has_gram_stain_outcome(culture, isolate):
    """
    Validator to check if this isolate has a Gram Stain recorded.
    """
    lab_number = culture.lab_number

    msg = f"{lab_number}: This patient has an isolate \
    entered without a Gram stain outcome recorded. Please add the \
    Gram stain outcome to all isolates in {lab_number}."

    if isolate.gram_stain:
        return True, None
    return False, msg

def has_date_positive(culture, isolate):
    """
    Validator to check if this isolate has a date positive recorded.
    """
    lab_number = culture.lab_number

    msg = f"{lab_number}: This patient has an isolate \
    entered without a date positive recorded. Please add the \
    date positive to all isolates in {lab_number}."

    if isolate.date_positive:
        return True, None
    return False, msg

def date_positive_after_date_ordered(culture, isolate):
    """
    Validator to check that the date positive for this isolate is after the
    sample date.
    """
    lab_number = culture.lab_number

    msg = f"{lab_number}: This patient has an isolate \
    entered where the date positive is before the date ordered. \
    Please add a plausibly correct date positive to all isolates in {lab_number}."

    # lack of dates is handled elsewhere so just bail
    if not isolate.date_positive:
        return True, None
    if not culture.date_ordered:
        return True, None

    if isolate.date_positive > culture.date_ordered:
        return True, None
    return False, msg


def validate(patient):
    """
    Given a PATIENT, determine whether they have enough
    data to remove them from the Blood culture list.

    Returns a tuple, a boolean IS_VALID, and a list of
    strings describing human readable errors.
    """
    is_valid = True
    errors = []

    # Does this patient have any blood cultures?
    if patient.bloodcultureset_set.count() == 0:
        errors = ['This patient has no blood culture results.\
        Please add at least one to remove them from the list.']
        return (False, errors)

    # TODO: restrict query to only relevant cultures, not old ones
    for culture in patient.bloodcultureset_set.all():

        valid, msg = has_labno(culture)
        if not valid:
            is_valid = False
            errors.append(msg)

        valid, msg = has_date_ordered(culture)
        if not valid:
            is_valid = False
            errors.append(msg)

        else:
            # We only check these for
            # cultures with lab numbers entered
            valid, msg = has_source(culture)
            if not valid:
                is_valid = False
                errors.append(msg)


            valid, msg = has_category(culture)
            if not valid:
                is_valid = False
                errors.append(msg)

        isolates = culture.isolates.all()

        for isolate in isolates:

            validators = [
                has_bottle_type,
                has_organism,
                has_gram_stain_outcome,
                has_date_positive,
                date_positive_after_date_ordered,
            ]

            for validator in validators:

                valid, msg = validator(culture, isolate)
                if not valid:
                    # we can have multiple isolates with no obvious identifier
                    # to use for them. Duplicate errors confuse Angular.
                    if msg not in errors:
                        is_valid = False
                        errors.append(msg)

    return (is_valid, errors)
