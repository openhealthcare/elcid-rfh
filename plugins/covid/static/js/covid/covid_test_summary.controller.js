angular.module('opal.controllers').controller('CovidTestSummaryView', function(
    $scope, $http, $q, $window
){
    "use strict";
    var vm = this;

    vm.data = {}

    var url = '/api/v0.1/covid_service_test_summary/';

    vm.load = function(patient_id){
        var patient_url = url + '' + patient_id + '/';

        $http({ url: patient_url, method: 'GET'}).then(
            function(response){
                vm.data = response.data;
            },
            function(){ $window.alert('Covid test summary could not be loaded') }
        )
    };

    vm.load($scope.patient.id);

});
