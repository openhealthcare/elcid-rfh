angular.module('opal.controllers').controller('RemoveStudyParticipantCtrl', function(
    study_id, participant_name, patient_id, $scope, $window, $http, $q, $modalInstance, $routeParams, ngProgressLite
){
    "use strict";

    var remove_url = '/api/v0.1/researchstudy-remove-participant/';

    $scope.study_id         = study_id;
    $scope.patient_id       = patient_id;
    $scope.participant_name = participant_name;
    $scope.reason           = null;

    $scope.remove_participant = function(){
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http.post(remove_url, {
            patient_id: $scope.patient_id,
            study_id  : $scope.study_id,
            reason    : $scope.reason
        }).then(
            function(response){
                $modalInstance.close('Closed');
                ngProgressLite.done();
                $window.location.reload()

            },
            function(){
                $modalInstance.close('cancel');
                ngProgressLite.done();
                $window.alert('Error: Unexpected issue removing patients');
            }

        );
    }

    $scope.cancel = function(){
        $modalInstance.close('cancel');
    }


});
