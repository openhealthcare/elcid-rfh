angular.module('opal.controllers').controller('EPMAView', function(
	$scope, $http, $q, $window, ngProgressLite
){
	"use strict";
	var vm = this;

	vm.epmaOrders = []

	// we display all fields coming from the api
	// chunked into arrays of 2
	vm.chunkedOrderFields = []

	// all the fields on the detail object
	vm.detailKeys = []

	var url_base = '/api/v0.1/epma_med_order/';

	vm.load = function(patient_id){
			var url = url_base + patient_id + '/';
			ngProgressLite.set(0);
			ngProgressLite.start();

			$http({cache: true, url: url, method: 'GET' }).then(
					function(response){
							vm.epmaOrders = response.data;
							if(vm.epmaOrders.length){
								vm.chunkedOrderFields = vm.getChunkedOrderFields(vm.epmaOrders);
								var hasDetail = _.findWhere(vm.epmaOrders, function(order){
									return order.details.length
								});
								vm.detailKeys = _.keys(hasDetail.details[0])
							}
							ngProgressLite.done();
					},
					function(){
							ngProgressLite.done();
							$window.alert('EPMA data could not be loaded');
					}
			);

	}



	vm.getChunkedOrderFields = function(obj){
		var keys = _.keys(obj);
		keys = _.without(keys, 'details')
		return _.chunk(keys, 2);
	}

	vm.load($scope.patient.id);

});
