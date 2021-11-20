angular.module('opal.services').factory('LabDetailLoader', function($http, $q) {
	"use strict";
	var labUrlBase = '/api/v0.1/lab_test/';

	var load = function(lab_number){
		var deferred = $q.defer();
		var url = labUrlBase + lab_number + '/';
		$http.get(url).then(function(response) {
				deferred.resolve(response.data);
		}, function() {
				console.error("unable to load in the lab test detail");
		});
		return deferred.promise;
	};

	return {
		load: load
	};
});
