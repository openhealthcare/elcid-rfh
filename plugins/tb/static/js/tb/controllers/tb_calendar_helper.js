angular.module('opal.controllers').controller('TBCalendarHelper',
	function($scope){
		"use strict"
		/*
		* This wraps the record editor, so that we edit the subrecords
		* on the js episode object.
		*
		* Then after we have done that we change the timestamp.
		* This causes the patientApi directive to reload the data
		* from the api endpoint.
		*/
		var self = this;
		this.getAddToMDT = function(addToMDT){
			return _.findWhere($scope.episode.add_to_mdt, {id: addToMDT.id});
		}

		this.timeStamp = Date.now();

		this.update = function(){
			self.timeStamp = Date.now();
		}

		this.add = function(){
			$scope.episode.recordEditor.newItem('add_to_mdt').then(self.update);
		}

		this.edit = function(add_to_mdt){
			$scope.episode.recordEditor.editItem(
				'add_to_mdt', self.getAddToMDT(add_to_mdt)
			).then(self.update);
		}
});
