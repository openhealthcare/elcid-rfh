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
            "Please place the patient in respiratory isolation as per Infection Prevention and Control Guidance. https://freenet2.royalfree.nhs.uk/documents/preview/110933/IPC-update-November-2022",
            "Use appropriate PPE, FFP3 mask and Decontaminate hands as per above trust IPC guidance.",
            "Patient contacts: o non-vulnerable groups no longer need to be swabbed unless they develop new symptoms and bay can be opened once Index patient is isolated.",
            "Vulnerable groups should be isolated and swabbed on alternate days for 7 days from the time index (positive) patient has been isolated. Otherwise, close the bay and continue swabbing the vulnerable contacts only.",
            "Upon discharge the room is to be terminally cleaned and (with VHP fogged only for long stay patient -discuss with IPC team).",
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
