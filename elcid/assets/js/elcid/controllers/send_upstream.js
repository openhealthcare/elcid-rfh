angular.module('opal.controllers').controller(
    'SendUpstreamCtrl',
    function($scope, $modalInstance, $http, $q, patient, item, callBack){
        $scope.send_upstream = function(){
            $http.put(
                '/api/v0.1/send_upstream/' + patient.id + '/',
                {item_id: item.id}
            ).then(function(){
                $q.when(callBack()).then(function(){
                    $modalInstance.close()
                })
            })

        $scope.cancel = function(){
            $modalInstance.close('cancel')
        }

    }
});
