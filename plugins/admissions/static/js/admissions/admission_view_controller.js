angular.module('opal.controllers').controller('AdmissionView', function(
    $scope, $http, $q, $window, ngProgressLite
){
    "use strict";
    var vm = this;

    vm.admissions = []

    var url_base = '/api/v0.1/admissions/';

    vm.load = function(patient_id){
        var url = url_base + '' + patient_id + '/';
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http({ cache: true, url: url, method: 'GET' }).then(
            function(response){
                vm.admissions = response.data;
                ngProgressLite.done();
            },
            function(){
                ngProgressLite.done();
                $window.alert('Admission data could not be loaded');
            }
        );

    }

    vm.load($scope.patient.id);

});
