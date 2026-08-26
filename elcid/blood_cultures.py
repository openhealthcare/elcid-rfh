"""
Utility module for blood cultures
"""

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

def validate(patient):
    """
    Given a PATIENT, determine whether they have enough
    data to remove them from the Blood culture list.

    Returns a tuple, a boolean IS_VALID, and a list of
    striungs describing human readable errors.
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

        else:
            # We only check for categorisation of
            # cultures with lab numbers entered
            valid, msg = has_category(culture)
            if not valid:
                is_valid = False
                errors.append(msg)

        isolates = culture.isolates.all()

        for isolate in isolates:

            valid, msg = has_organism(culture, isolate)
            if not valid:
                is_valid = False
                errors.append(msg)

            valid, msg = has_gram_stain_outcome(culture, isolate)
            if not valid:
                is_valid = False
                errors.append(msg)


    return (is_valid, errors)
