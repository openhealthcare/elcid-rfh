angular.module('opal.controllers').controller(
    'BCAddToListCtrl',
    function($scope, $http, $window, $modalInstance){
        "use strict";

        $scope.states = {
            INITIAL: 'initial',
            INVALID: "invalid",
            CONFIRM: "confirm",
        };
        $scope.state = $scope.states.INITIAL;

        $scope.mrn = null;

        $scope.search = function(){
            $http.get('/elcid/v0.1/blood_culture_list_viability/?mrn='+$scope.mrn).then(
                function(result){
                    if(result.data.valid){
                        $scope.state = $scope.states.CONFIRM;
                        return
                    }
                    if(!result.data.valid){
                        $scope.state = $scope.states.INVALID;
                        $scope.errors = result.data.errors;
                        return
                    }
                    return

                }
            )
        }

        $scope.add = function(){
            $http.post('/elcid/v0.1/blood_culture_list_viability/', {mrn:$scope.mrn}).then(
                function(result){
                    $modalInstance.close('added');
                    $window.location.reload()
                }
            )
        }

        $scope.cancel = function(){
            $modalInstance.close('cancel');
        }


    });
