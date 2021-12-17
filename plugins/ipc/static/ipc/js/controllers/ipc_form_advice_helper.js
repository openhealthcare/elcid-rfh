angular.module('opal.controllers').controller(
	'IPCFormAdviceHelper',
	function($scope){
		var self = this;
		var MRSA_NASEPTIN = [
			"MRSA has been isolated from ………",
			"Mupirocin Resistant on ……",
			"Please start cycle one of MRSA decolonisation protocol. Naseptin (chlorexidhine-neomycin 0.1% -0.5%) nasal cream (QDS) with chlorexidhine 4% daily body wash and alternate days hair wash for a duration of 10 days",
			"*	Place in contact isolation.",
			"*	Inform the patient of results and document conversation in the notes.",
			"*	Offer the patient information leaflet",
			"*	Gloves and apron to be worn by anyone entering the room.",
			"*	Remove PPE and decontaminate hands before leaving the room",
			"*	If MRSA infection is suspected antibiotic advice is available from the Consultant Microbiologist",
		].join("\n")

		var MRSA_MUPIROCIN= [
			"MRSA has been isolated from ……",
			"Mupirocin sensitive on …….",
			"Please start cycle one of MRSA decolonisation protocol. Mupirocin 2% nasal ointment (TDS) with chlorexidhine 4% daily body wash and alternate days hair wash for a duration of 5 days:",
			"*	Place in contact isolation.",
			"*	Inform the patient of results and document conversation in the notes.",
			"*	Offer the patient information leaflet",
			"*	Gloves and apron to be worn by anyone entering the room.",
			"*	Remove PPE and decontaminate hands before leaving the room",
			"*	If MRSA infection is suspected antibiotic advice is available from the Consultant      Microbiologist",
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
		this.goToCursor = function(pos){
			setTimeout(function(){
				var elem = $('textarea[name="_clinical_discussion"]');
				elem.focus();
				elem.prop('selectionEnd', pos);
			}, 1);
		}
		this.addMRSNaseptin = function(){
			self.addText(MRSA_NASEPTIN);
			self.goToCursor(28);
		}
		this.addMRSAMupirocin = function(){
			self.addText(MRSA_MUPIROCIN);
			self.goToCursor(28);
		}
	}
)
