angular.module('opal.controllers').controller('DeleteStudyCtrl', function(
    study_id, $scope, $window, $http, $q, $modalInstance, ngProgressLite
){
    "use strict";

    var url = '/api/v0.1/researchstudy/' + study_id + '/';

    $scope.name = null;

    $scope.delete_study = function(){
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http['delete'](url).then(
            function(response){
                $modalInstance.close('Deleted');
                $window.location = "/#/research/";
            },
            function(){
                ngProgressLite.done();
                $window.alert('Error: Could not delete study');
            }

        );
    }

    $scope.cancel = function(){
        $modalInstance.close('cancel');
    }

});
