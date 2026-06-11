angular.module('opal.controllers').controller('CloseStudyCtrl', function(
    study_id, $scope, $window, $http, $q, $modalInstance, ngProgressLite
){
    "use strict";

    var url = '/api/v0.1/researchstudy-close/';

    $scope.name = null;

    $scope.delete_study = function(){
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http.post(url, {'state': 'CLOSED', 'study_id': study_id}).then(
            function(response){
                $modalInstance.close('Closed');
                ngProgressLite.done();
                $window.location.reload()
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
