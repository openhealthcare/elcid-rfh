angular.module('opal.controllers').controller('BedStatus', function(
	$scope, $http, queryResponse
){
	"use strict";
	$scope.patients = queryResponse.data;

	$scope.isolate = function(bedStatus, inIsolation){
		var args = {in_isolation: inIsolation}
		$http.put('/api/v0.1/bed_status/' + bedStatus.id + '/isolate/', args).then(
			function(){
				bedStatus.in_isolation = inIsolation;
			}
		)
	}
});
