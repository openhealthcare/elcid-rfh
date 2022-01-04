angular.module('opal.controllers').controller(
    'SendUpstreamCtrl',
    function($scope, $modalInstance, $http, patient, item, refresh_patient, refresh_timeline){

        $scope._patient         = patient;
        $scope.item             = item;
        $scope.detail_refresh   = refresh_patient;
        $scope.refresh_timeline = refresh_timeline;

        $scope.send_upstream = function(){
            $http.put('/api/v0.1/send_upstream/' + item.id + '/').then(
                function(response){
                    $scope.detail_refresh().then(
                        function(){
                            $scope.refresh_timeline();
                            $modalInstance.close();
                        }
                    )
                }
            )
        }

        $scope.cancel = function(){
            $modalInstance.close('cancel');
        }

    }
);
