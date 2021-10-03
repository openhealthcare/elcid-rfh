"""
Constants for the IPC Plugin
"""
IPC_ROLE = "ipc_user"



ADVICE = {
    'other': '',
    'mrsa_neg': '',
    'multi_drug_resistant_organism': 'Strict contact isolation precaution. Screen on admission and inform IPC nurses',
    'carb_resistance': 'Strict isolation. Screen on admission. Inform IPC nurses',
    'contact_of_candida_auris': 'Strict contact isolation precaution. Screen on admission and inform IPC nurses',
    'vre': 'Contact isolation (Enteric isolation with diarrhoea). Inform IPC nurses',
    'contact_of_covid_19': 'Respiratory Precautions.Screen on admission and inform IPC nurses',
    'reactive': 'No requirement to isolate, screen on admission',
    'contact_of_carb_resistance': ' Screen on admission. Inform IPC nurses.',
    'contact_of_acinetobacter': 'Strict isolation. Screen on admission. Inform IPC nurses.',
    'mrsa': 'Contact isolation and screen on admission',
    'c_difficile': 'Enteric isolation. Inform IPC nurses',
    'vre_neg': 'No requirement to isolate (Enteric isolation with diarrhoea). Inform IPC nurses',
    'candida_auris': 'Strict contact isolation precaution. Screen on admission and inform IPC nurses',
    'covid_19': 'Respiratory Precautions.Screen on admission and inform IPC nurses',
    'cjd': 'Contact Microbiology or Infection Control team on admission',
    'acinetobacter': 'Strict isolation. Screen on admission. Inform IPC nurses.'
}




ALERT_DISPLAY = {
    'other': 'Other',
    'mrsa_neg': 'MRSA Neg',
    'multi_drug_resistant_organism': 'Multi drug resistant organism',
    'carb_resistance': 'Carb resistance',
    'contact_of_candida_auris': 'Contact of Candida auris',
    'vre': 'VRE',
    'contact_of_covid_19': 'Contact of Covid-19',
    'reactive': 'Reactive',
    'contact_of_carb_resistance': 'Contact of Carb resistance',
    'contact_of_acinetobacter': 'Contact of Acinetobacter',
    'mrsa': 'MRSA',
    'c_difficile': 'C Difficile',
    'vre_neg': 'VRE Neg',
    'candida_auris': 'Candida auris',
    'covid_19': 'COVID-19',
    'cjd': 'CJD',
    'acinetobacter': 'Acinetobacter'
}
