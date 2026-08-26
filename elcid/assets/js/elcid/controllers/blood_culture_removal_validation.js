angular.module('opal.controllers').controller(
    'BCRemovalValidationCtrl',
    function($scope, $http, $window, $modalInstance, episode, remove_callback, hide_actions){
        "use strict";

        var demographics = episode.demographics[0];
        var patient_id = demographics.patient_id;
        var episode_id = episode.id;
        var patient_link = '/#/patient/' + patient_id + '/' + episode_id

        $scope.state = 'initial'
        $scope.name = demographics.first_name + ' ' + demographics.surname
        $scope.override_reason = null;
        $scope.hide_actions = hide_actions;

        $scope.states = {
            INITIAL: "initial",
            INVALID: "invalid",
            CONFIRM: "confirm",
            OVERRIDE: "override",
        }

        $scope.remove = function(){
            // TODO IMPLEMENT
        }

        $scope.state = $scope.states.INITIAL;

        $http.get('/elcid/v0.1/blood_culture_validation/' + patient_id + '/').then(function(result){
            if(result.data.valid){
                $scope.state = $scope.states.CONFIRM
                return
            }
            if(!result.data.valid){
                $scope.state = $scope.states.INVALID;
                $scope.errors = result.data.errors;
                return
            }
            return
        })

        $scope.override = function(){
            $scope.state = $scope.states.OVERRIDE;
        }

        $scope.go_to_patient = function(){
            $modalInstance.close('cancel');
            $window.location = patient_link;
        }

        $scope.cancel = function(){
            $modalInstance.close('cancel');
        }

    });
