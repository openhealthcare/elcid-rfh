angular.module('opal.controllers').controller(
    'AddToServiceCtrl',
    function($scope, $modalInstance, $http, profile, patient, refresh) {

        $scope.patient        = patient;
        $scope.detail_refresh = refresh;

        var ADDABLE = ['TB', 'COVID-19']

        var current_categories = _.pluck(patient.episodes, "category_name")

        if( profile.has_role('ipc_user') ){ // CONSTANT FROM plugins.ipc.constants
            ADDABLE.push('IPC');
        }

        $scope.currently_addable = _.reject(
            ADDABLE, function(x){ return current_categories.indexOf(x) != -1 });

        $scope.add = function(what){
            $http.put('/api/v0.1/add_to_service/' + $scope.patient.id + '/',
                      {category_name: what}).then(
                          function(response){
                              $scope.detail_refresh().then(
                                  function(){
                                      $modalInstance.close();
                                  }
                              );
                          }
                      )
        };

        $scope.cancel = function() {
            $modalInstance.close('cancel');
        };
    }
);
