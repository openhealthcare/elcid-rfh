angular.module('opal.controllers').controller(
    'IPCFormAdviceHelper',
    function($scope){
	var self = this;

	self.MUPIROCIN_SENSITIVE = [
	    "MRSA has been isolated from _____",
	    "",
	    "",
	    "Mupirocin sensitive on _____",
	    "Please start cycle one of MRSA decolonisation protocol. Mupirocin 2% nasal ointment (TDS) with chlorexidhine 4% daily body wash for 5 days duration and Days 1 & 5 for Hair wash (Twice during the five days regime). ",
	    "* Place in contact isolation",
	    "* Inform the patient of results and document conversation in the notes",
	    "* Offer the patient information leaflet",
	    "* Gloves and apron to be worn by anyone entering the room",
	    "* Remove PPE and decontaminate hands before leaving the room",
            "* Upon discharge the room is to be terminally cleaned.",
	    "* If MRSA infection is suspected antibiotic advice is available from the consultant microbiologist",
	].join("\n")

	self.MUPIROCIN_RESISTANT = [
	    "MRSA has been isolated from _____",
	    "",
	    "",
	    "Mupirocin Resistant on _____",
	    "Please start cycle one of MRSA decolonisation protocol. Naseptin (chlorexidhine-neomycin 0.1% -0.5%) nasal cream (QDS) for a duration of 10 days",
            "Chlorexidhine 4% Daily body wash for 5 days duration and Days 1 & 5 for Hair wash (Twice during the five days regime).",
	    "* Place in contact isolation",
	    "* Inform the patient of results and document conversation in the notes",
	    "* Offer the patient information leaflet",
	    "* Gloves and apron to be worn by anyone entering the room",
	    "* Remove PPE and decontaminate hands before leaving the room",
            "* Upon discharge the room is to be terminally cleaned.",
	    "* If MRSA infection is suspected antibiotic advice is available from the consultant microbiologist",
	].join("\n")

	self.C_DIFFICILE = [
	    "C. difficile toxin/ PCR has been isolated from a stool specimen collected on: _____",
	    "",
	    "",
	    "* Please place the patient in Enteric isolation",
	    "* Use PPE for any contact with the patient or their environment",
	    "* Remove PPE and wash hands with soap and water before leaving the room",
	    "* Inform the patient of results and document conversation in the notes",
	    "* Offer the patient information leaflet",
	    "* Please review the antibiotics and refer to Clostridium difficile management policy on the intranet",
	    "* Upon discharge the room is to be terminally cleaned and VHP fogged",
	    "* Contact Infection Prevention & Control Team for further advice",
	].join("\n")

	self.CONTACT = [
	    "Infection Prevention & Control Alert - contact",
	    "",
	    "",
	    "The micro-organism _____",
	    "Has been isolated from _____",
	    "The sample was taken on _____",
	    "* Please place the patient in contact isolation",
	    "* Gloves and apron to be worn by anyone entering the room",
	    "* Remove PPE and decontaminate hands before leaving the room",
	    "* Upon discharge the room is to be terminally cleaned",
	    "* Contact Infection Prevention & Control Team for further advice",
	].join("\n")

	self.MULTI_RESISTANT = [
            "A Multi-resistant organism CPE / CPO",
            "",
            "",
            "Has been isolated from _____. on _____",
            "* Please place the patient in strict contact isolation",
            "* The doors should remain closed at all times",
            "* Gloves and apron to be worn by anyone entering the room",
            "* PPE to be removed and hands decontaminated before leaving the room",
            "* Inform the patient of results and document conversation in the notes",
            "* Offer the patient information leaflet",
            "* Reusable equipment, where possible are to remain in the room until the patient is discharged",
            "* Upon discharge the room is to be terminally cleaned and VHP fogged",
            "* Contact Infection Prevention & Control Team for further advice"
	].join("\n")


	self.RESPIRATORY = [
	    "Infection Prevention & Control Alert - respiratory",
	    "",
	    "",
	    "The micro-organism RSV (Respiratory Syncytial Virus)/Rhinovirus",
	    "Has been isolated from Nasopharyngeal swab / Throat swab.",
	    "The sample was taken on _____",
	    "* Please place the patient in respiratory isolation",
	    "* Gloves apron and FFP 3 mask to be worn by anyone entering the room",
	    "* Remove PPE and decontaminate hands before leaving the room",
	    "* Upon discharge the room is to be terminally cleaned",
	    "* Contact Infection Prevention & Control Team for further advice",
            "",
            "Stepping down IPC measures:",
            "",
            "Not immunocompromised patients/ not ITU/Not on high-risk wards",
            " * 5 days from symptoms onset",
            " * Improving clinical features of acute viral illness",
            " * Afebrile for 24 hours off antipyretic agents.",
            "",
            "Severe immunocompromised patients/ ITU/high risk wards",
            " * 5 days from symptoms onset",
            " * Improving clinical features of acute viral illness",
            " * Afebrile for 24 hours off antipyretic agents.",
            " * 1 negative Respiratory PCR result (NPS swab)"

	].join("\n")

	self.COVID = [
	    "Infection Prevention & Control Alert - respiratory",
	    "",
	    "",
            "The patient has been tested Positive for SARS CoV-2 the virus causing COVID 19 disease",
            "The sample was taken on ______ · Please inform the patient of results and document conversation in the notes.",
            "Please place the patient in respiratory isolation as per Infection Prevention and Control Guidance.",
            "https://freenet.royalfree.nhs.uk/download_file/5eb47fce-2b53-4b88-b113-8cd2e0f6d5cd/5709",
            "https://freenet.royalfree.nhs.uk/download_file/d13b9cd7-bb5f-4039-844f-d211205c7890/5709",
            "Use appropriate PPE, FFP3 mask and Decontaminate hands as per above trust IPC guidance.",
            "Patient contacts: Monitor patient contacts for 5 days, asymptomatic swabbing is not required, unless they develop new symptoms, please inform IPCT.",
            "Bay can be opened once Index patient is isolated and bedspace is terminally cleaned and the curtains changed.",
            "If a second case is detected in a multi-occupancy bay, the bay is temporarily closed to all admissions pending review by the IPC team.",
            "Upon discharge the room is to be terminally cleaned.",
            "Contact Infection Prevention & Control Team for further advice."
	].join("\n")

        self.VRE = [
            "Infection Prevention & Control Alert – enteric/contact",
            "",
            "", 
            "The micro-organism Vancomycin-Resistant Enterococcus (VRE) faecium/faecalis/ Extended Spectrum Beta-Lactamase (ESBL)",
            "has been isolated from _____ ",
            "The sample was taken on ______",
            "Please place the patient in enteric/contact isolation",
            "Gloves and apron to be worn by anyone entering the room",
            "Remove PPE and decontaminate hands before leaving the room",
            "Upon discharge the room is to be terminally cleaned",
            "Contact Infection Prevention & Control Team for further advice."
        ].join("\n")

        self.NOROVIRUS = [
            "Norovirus/Rotavirus/Sapovirus has been detected from a stool specimen collected on ____",
            "Please place the patient in Enteric isolation",
            "Use PPE for any contact with the patient or their environment.",
            "Remove PPE and wash hands with soap and water before leaving the room.",
            "Inform the patient of results and document conversation in the notes.",
            "Offer the patient information leaflet",
            "Upon discharge the room is to be terminally cleaned and VHP fogged.",
            "Contact Infection Prevention & Control Team for further advice."
        ].join("\n")

        self.ENTERIC = [
            "______ has been isolated from a stool specimen collected on _____",
            " * Please place the patient in Enteric isolation",
            " * Use PPE for any contact with the patient or their environment.",
            " * Remove PPE and wash hands with soap and water before leaving the room.",
            " * Inform the patient of results and document conversation in the notes.",
            " * Upon discharge the room is to be terminally cleaned.",
            " * Contact Infection Prevention &amp; Control Team for further advice."
        ].join("\n")

        self.INFLUENZA = [
            "Infection Prevention & Control Alert - respiratory",
            "",
            " * The micro-organism Influenza A/B.",
            " * Detected on Nasopharyngeal swab",
            " * The sample was taken on ______",
            " * Please place the patient in respiratory isolation",
            " * Gloves, apron and FFP3 mask to be worn by anyone entering the room",
            " * Remove PPE and decontaminate hands before leaving the room.",
            " * Upon discharge the room is to be terminally cleaned",
            " * Please assess to ascertain whether patient contacts and arrange prophylaxis where indicated",
            " * Contact Infection Prevention & Control Team for further advice",
            "",
            "All patients at risk of OR suffering from complicated influenza should receive treatment.",
            "Patients at risk of complicated Influenza:",
            " * neurological, hepatic, renal, pulmonary, and chronic disease",
            " * diabetes mellitus",
            " * severe immunosuppression",
            " * age over 65 years",
            " * pregnancy (including up to 2 weeks post-partum)",
            " * children under 6 months",
            " * morbid obesity (BMI =40)",
            "Patients suffering from complicated influenza:",
            "Influenza requiring hospital admission",
            "AND/OR",
            "with symptoms and signs of lower respiratory tract infection, central",
            "nerrvous system involvement",
            "AND/OR",
            "a significant exacerbation of an underlying medical condition.",
            "Influenza treatment:",
            " First line: Oseltamivir 75mg BD PO for 5 days. For any queries, please",
            "contact/discuss with virology team.",
            "See RFL Microguide and UKHSA guidance for further treatment advice,",
            "Including dosing in renal impairment and in children.",
            "UKHSA guidance:",
            "https://www.gov.uk/government/publications/influenza-treatment-and-prophylaxis-using-anti-viral-agents.",
        ].join("\n")

        self.INFLUENZA_CONTACT = [
            "Infection Prevention & Control Alert - Influenza contact",
            "",
            "This patient has been identified as a Contact of Influenza A/B on _____",
            "Please review patient for symptoms of influenza:",
            "If this patient is symptomatic: Place in respiratory isolation and send nasopharyngeal swab for influenza PCR",
            "If this patient is asymptomatic or influenza PCR negative within past 24 hours: Please review whether patient at risk of complicated influenza:",
            " * neurological, hepatic, renal, pulmonary, and chronic disease",
            " * diabetes mellitus",
            " * severe immunosuppression",
            " * age over 65 years",
            " * pregnancy (including up to 2 weeks post-partum)",
            " * children under 6 months",
            " * morbid obesity (BMI =40)",
            "",
            "Asymptomatic/ influenza PCR negative patients at risk of complicated influenza should be receive antiviral prophylaxis prescribed by their treating clinical team:",
            " * First line: Oseltamivir 75mg OD PO for 10 days. For any queries, pleasecontact/discuss with Virology team.",
            " * See RFL Microguide and UKHSA guidance for further prophylaxis advice,including dosing in renal impairment and in children",
            " * Routine swabbing is not advised in contacts. However, diagnostic sampling of the contacts for influenza virus detection is recommended before or at the time of commencing antiviral prophylaxis in immunosuppressed patients and critically ill patients",
            " * UKHSA guidance: https://www.gov.uk/government/publications/influenza-treatment-and-prophylaxis-using-anti-viral-agents.",
        ].join("\n")

        self.COVID_CONTACT = [
            "Infection Prevention & Control Alert – Respiratory",
            "",
            "The patient has been identified as a Covid Contact of an individual who is tested positive SARS CoV-2, the virus causing COVID 19 disease",
            "The last day of contact was on ___",
            "Please send Covid swabs every other day for next 7 days, until ____ ",
            "(count from the day index patient was isolated)",
            "Please inform the patient and document conversation in the medical record.",
            "If for discharge to other healthcare facilities i.e. nursing home, rehab or others please inform the unit.",
            "Please place the patient in respiratory isolation as per Infection Prevention and Control Guidance :",
            "https://freenet2.royalfree.nhs.uk/documents/preview/110933/IPC-update-November-2022",
            "Use appropriate PPE, FFP3 mask and decontaminate hands as per above trust IPC guidance.",
            "",
            "Patient contacts:",
            " * Non-vulnerable groups no longer need to be swabbed unless they develop new symptoms and bay can be opened once Index patient is isolated.",
            " * Vulnerable groups should be isolated and swabbed on alternate days for 7 days from the time index (positive) patient has been isolated. Otherwise, close the bay and continue swabbing the vulnerable contacts only.",
            " * Upon discharge the room is to be terminally cleaned and curtain changed.",
            " * Contact Infection Prevention & Control Team for further advice.",
        ].join("\n")

	this.addText = function(text){
	    var discussion = $scope.formItem.editing.clinical_discussion;
	    if(discussion){
		discussion += "\n";
	    }
	    else{
		discussion = "";
	    }
	    $scope.formItem.editing.clinical_discussion = discussion + text;
	}
    }
)
