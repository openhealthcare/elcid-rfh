angular.module('opal.controllers').controller(
    'TBMDTNoActionCtrl',
    function($scope, $modalInstance, $http, patient_id) {

        $scope.patient_id = patient_id;

        $scope.no_action = function(what){
            $http.put('/api/v0.1/tb_mdt_no_action/' + $scope.patient_id + '/',
                      {}).then(
                          function(response){
                              window.location.reload();
                          }
                      )
        };

        $scope.cancel = function() {
            $modalInstance.close('cancel');
        };
    }
);
