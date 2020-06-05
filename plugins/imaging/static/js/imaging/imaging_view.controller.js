angular.module('opal.controllers').controller('ImagingView', function(
    $scope, $http, $q, $window, ngProgressLite
){
    "use strict";
    var vm = this;

    vm.imaging = []

    var url_base = '/api/v0.1/imaging/';

    vm.load = function(patient_id){
        var url = url_base + '' + patient_id + '/';
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http({ cache: true, url: url, method: 'GET' }).then(
            function(response){
                vm.imaging = response.data;
                ngProgressLite.done();
            },
            function(){
                ngProgressLite.done();
                $window.alert('Imaging data could not be loaded');
            }
        );

    }

    vm.load($scope.patient.id);

});
