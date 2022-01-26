angular.module('opal.controllers').controller('EPMAView', function(
	$scope, $http, $q, $window, ngProgressLite
){
	"use strict";
	var vm = this;

	vm.imaging = []

	var url_base = '/api/v0.1/epma_med_order/';

	vm.load = function(patient_id){
			var url = url_base + patient_id + '/';
			ngProgressLite.set(0);
			ngProgressLite.start();

			$http({cache: true, url: url, method: 'GET' }).then(
					function(response){
							vm.epmaOrders = response.data;
							ngProgressLite.done();
					},
					function(){
							ngProgressLite.done();
							$window.alert('EPMA data could not be loaded');
					}
			);

	}

	vm.chunkedOrderFields = function(obj){
		var keys = _.keys(obj);
		keys = _.without(keys, 'details')
		return _.chunk(keys, 2);
	}

	vm.load($scope.patient.id);

	vm.keys = _.keys;
});
