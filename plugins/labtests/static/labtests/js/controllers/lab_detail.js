angular.module('opal.controllers').controller('LabDetail', function(
	$scope, lab_number, lab_data
){
	"use strict";
	$scope.lab_number = lab_number;
	$scope.lab_data = lab_data;
});
