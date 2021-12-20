angular.module('opal.controllers').controller('BedStatus', function(
	$scope, queryResponse
){
	"use strict";
	$scope.patients = queryResponse.data;

	$scope.isolate = function(bedStatus, isIsolated){
		var args = {is_isolated: isIsolated}
		$http.put('/api/v0.1/bed_status/' + bedStatus.id + '/isolate/', args).then(
			function(){
				bedStatus.in_isolation = isIsolated;
			}
		)
	}
});
