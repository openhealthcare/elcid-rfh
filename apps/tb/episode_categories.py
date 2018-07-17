from opal.core import episodes


class TbEpisode(episodes.EpisodeCategory):
    display_name = 'TB'
    detail_template = 'detail/tb.html'

    # contact has been flagged as a potential risk
    NEW_CONTACT = "New Contact"

    # contact has been referred either through contact screening
    # or a direct referral
    NEW_REFERRAL = "New Referral"
    ASSESSED = "Assessed"
    ACTIVE_TB_TREATMENT = "Active TB Treatment"
    LATENT_TB_TREATMENT = "Latent TB Treatment"
    NTM_TREATMENT = "NTM Treatment"

    # patient has gone through the initial assessment and tests
    # have probably been sent off
    UNDER_INVESTIGATION = "Under Investigation"

    # patient has been discharged
    DISCHARGED = "Discharged"

    stages = [
        NEW_CONTACT,
        NEW_REFERRAL,
        ASSESSED,
        ACTIVE_TB_TREATMENT,
        LATENT_TB_TREATMENT,
        NTM_TREATMENT,
        UNDER_INVESTIGATION,
        DISCHARGED
    ]
