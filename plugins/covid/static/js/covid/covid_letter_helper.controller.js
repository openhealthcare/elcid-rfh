angular.module('opal.controllers').controller('CovidLetterHelper', function(
	$http
){
	"use strict";
	var self = this;
	self._hasBeenWritten = null;

	self.requestUpstream = _.once(function(modelApiName, itemId){
		/*
		* Requests from upstream whether this has been submitted upstream
		* this will only ever be called once. If the item is subsequently sent
		* the front end is updated by markAsWritten.
		*/
		var url = "/api/v0.1/epr_" + modelApiName + "/" + itemId + "/";
		$http.get(url).then(function(response){
			self._hasBeenWritten = response.data.sent
		})
	});

	self.isWrittenToEPR = function(modelApiName, itemId){
		/*
		* If haven't set the _hasBeenWritten, request upstream
		* to see if its been written
		*/
		if(_.isNull(self._hasBeenWritten)){
			self.requestUpstream(modelApiName, itemId);
		}
		return self._hasBeenWritten;
	}

	self.markAsWritten = function(){
		self._hasBeenWritten = true;
	}
});
