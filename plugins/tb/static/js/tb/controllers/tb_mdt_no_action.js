angular.module('opal.controllers').controller(
    'TBMDTNoActionCtrl',
    function($scope, $modalInstance, $http, patient_id, name) {
        $scope.name = name;
        $scope.no_action = function(what){
            $http.put('/api/v0.1/tb_mdt_no_action/' + patient_id + '/',
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
