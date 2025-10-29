"""
Render OPAT MDT notes for EPR
"""

def add_section(text, title, section):
    """
    Given a note section, add it to TEXT
    """
    return text + "\n\n" + title + "\n\n" + section

def render_opat_advice(advice):
    """
    Given a MicrobiologyInput instance that contains OPAT advice,
    render this advice with an OPAT advice template
    """
    text       = ""
    episode    = advice.episode
    record     = episode.opatrecord_set.first()
    background = episode.relevantopatbackground_set.get()

    text = add_section(text, "Referral:", f"{record.referral_date} {record.referral_source}")

    text = add_section(text, "Chronic Infection and key issues", record.indication)

    text = add_section(text, "Relevant Background:", background.details)

    text = add_section(text, "Microbiology:", record.microbiology)

    radiology_text = "\n".join([
        f"{i.imaging_type} {i.details}" for i in episode.imaging_set.all()
    ])

    text = add_section(text, "Radiology:", radiology_text)

    allergy_text = "\n".join([
        f"{i.drug}" for i in episode.patient.allergies_set.all()
    ])

    text = add_section(text, "Antibiotic allergies:", allergy_text)

    text = add_section(text, "Clinical Discussion:", advice.clinical_discussion)

    text = add_section(text, "Infection Control:", advice.infection_control)

    text = add_section(text, "Agreed Plan:", advice.agreed_plan)
    return text
