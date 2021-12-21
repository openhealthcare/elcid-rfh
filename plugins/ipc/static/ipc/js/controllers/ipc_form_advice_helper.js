angular.module('opal.controllers').controller(
	'IPCFormAdviceHelper',
	function($scope){
		var self = this;

		self.MUPIROCIN_SENSITIVE = [
			"MRSA has been isolated from .....",
			"Mupirocin sensitive on .....",
			"Please start cycle one of MRSA decolonisation protocol. Mupirocin 2% nasal ointment (TDS) with chlorexidhine 4% daily body wash and alternate days hair wash for a duration of 5 days:",
			"* Place in contact isolation.",
			"* Inform the patient of results and document conversation in the notes.",
			"* Offer the patient information leaflet.",
			"* Gloves and apron to be worn by anyone entering the room.",
			"* Remove PPE and decontaminate hands before leaving the room.",
			"* If MRSA infection is suspected antibiotic advice is available from the Consultant Microbiologist.",
		].join("\n")

		self.MUPIROCIN_RESISTANT = [
			"MRSA has been isolated from .....",
			"Mupirocin Resistant on .....",
			"Please start cycle one of MRSA decolonisation protocol. Naseptin (chlorexidhine-neomycin 0.1% -0.5%) nasal cream (QDS) with chlorexidhine 4% daily body wash and alternate days hair wash for a duration of 10 days",
			"* Place in contact isolation.",
			"* Inform the patient of results and document conversation in the notes.",
			"* Offer the patient information leaflet.",
			"* Gloves and apron to be worn by anyone entering the room.",
			"* Remove PPE and decontaminate hands before leaving the room.",
			"* If MRSA infection is suspected antibiotic advice is available from the Consultant Microbiologist.",
		].join("\n")


		self.C_DIFFICILE = [
			"C. difficile toxin/ PCR has been isolated from a stool specimen collected on: .....",
			"* Please place the patient in Enteric isolation",
			"* Use PPE for any contact with the patient or their environment.",
			"* Remove PPE and wash hands with soap and water before leaving the room.",
			"* Inform the patient of results and document conversation in the notes.",
			"* Offer the patient information leaflet.",
			"* Please review the antibiotics and refer to Clostridium difficile Management policy on the intranet.",
			"* Upon discharge the room is to be terminally cleaned and VHP fogged.",
			"* Contact Infection Prevention & Control Team for further advice.",
		].join("\n")

		self.MICRO_ORGANISM = [
			"Infection Prevention & Control Alert - contact",
			"The micro-organism .....",
			"* Has been isolated from .....",
			"* The sample was taken on .....",
			"* Please place the patient in contact isolation.",
			"* Gloves and apron to be worn by anyone entering the room.",
			"* Remove PPE and decontaminate hands before leaving the room.",
			"* Upon discharge the room is to be terminally cleaned.",
			"* Contact Infection Prevention & Control Team for further advice.",
		].join("\n")

		self.MULTI_RESISTANT = [
			"Infection Prevention & Control Alert - respiratory",
			"",
			"",
			"* The micro-organism .....",
			"* Has been isolated from Nasopharyngeal swab / Throat swab.",
			"* The sample was taken on .....",
			"* Please place the patient in respiratory isolation.",
			"* Gloves apron and FFP 3 mask to be worn by anyone entering the room.",
			"* Remove PPE and decontaminate hands before leaving the room.",
			"* Upon discharge the room is to be terminally cleaned.",
			"* Contact Infection Prevention & Control Team for further advice.",
		].join("\n")

		self.COVID = [
			"Infection Prevention & Control Alert - respiratory",
			"* The patient has been tested positive for SARS  CoV-2  the virus causing  COVID 19 disease",
			"* The sample was taken on",
			"* Please inform the patient of results and document conversation in the notes.",
			"* Please place the patient in respiratory isolation as per Infection Prevention and Control Guidance",
			"* Use appropriate PPE and Decontaminate hands",
			"* Upon discharge the room is to be terminally cleaned and VHP fogged",
			"* Contact Infection Prevention & Control Team for further advice.",
			"* Please assess for any patient contacts: those sharing the same bay, who are not suspected or confirmed COVID themselves. Patient contacts should be monitored for features of COVID illness for 14 days and should be provided with written stay at home advice if discharged prior to the 14 day period.",
			"* [https://www.gov.uk/government/publications/covid-19-stay-at-home-guidance/stay-at-home-guidance-for-households-with-possible-coronavirus-covid-19-infection](https://www.gov.uk/government/publications/covid-19-stay-at-home-guidance/stay-at-home-guidance-for-households-with-possible-coronavirus-covid-19-infection).",
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
