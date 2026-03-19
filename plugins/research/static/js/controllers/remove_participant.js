angular.module('opal.controllers').controller('RemoveStudyParticipantCtrl', function(
    study_id, participant_name, patient_id, $scope, $window, $http, $q, $routeParams, ngProgressLite
){
    "use strict";

    var remove_url = '/api/v0.1/researchstudy-remove-participant/';

    $scope.study_id         = study_id;
    $scope.patient_id       = patient_id;
    $scope.participant_name = participant_name;

    $scope.remove_participant = function(){
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http.post(remove_url, {
            patient_id: $scope.patient_id,
            study_id  : $scope.study_id
        }).then(
            function(response){
                ngProgressLite.done();
                $window.location = response.data.url;
            },
            function(){
                ngProgressLite.done();
                $window.alert('Error: Unexpected issue adding patients');
            }

        );
    }

    $scope.cancel = function(){
        $modalInstance.close('cancel');
    }


});
