angular.module('opal.controllers').controller('AppointmentView', function(
    $scope, $http, $q, $window, ngProgressLite
){
    "use strict";
    var vm = this;

    vm.appointments = []

    var url = '/api/v0.1/appointments/';

    vm.load = function(patient_id){
        var patient_url = url + ''+ patient_id + '/';
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http({ cache: true, url: patient_url, method: 'GET'}).then(
            function(response){
                vm.appointments = response.data
                ngProgressLite.done();
            },
            function(){
                ngProgressLite.done();
                $window.alert('Appointment data could not be loaded')
            }
        )
    };

    vm.load($scope.patient.id);

});
