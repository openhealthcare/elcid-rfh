angular.module('opal.services').service('StarObservation', function($http){
	"use strict";
	var url = '/api/v0.1/star_observation/'
	return {
		starObservation: function(patient_id, test_name, lab_number, observation_name, observation){
			var toSave = {
				patient_id: patient_id,
				test_name: test_name,
				lab_number: lab_number,
				observation_name: observation_name,
			}
			$http.post(url, toSave).then(function(createdStar) {
				observation.star = createdStar.data.id;
			});
		},
		unstarObservation: function(observation){
			var deleteUrl = url + observation.star + '/'
			$http.delete(deleteUrl).then(function(){
				observation.star = undefined;
			})
		}
	}
});
