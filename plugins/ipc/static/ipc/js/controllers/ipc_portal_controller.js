angular.module('opal.controllers').controller(
    'IPCPortalCtrl',
    function($scope, $http, ngProgressLite) {


        $scope.query = '';

        $scope.reset_search = function(){
            $scope.patient = null;
            $scope.patient_not_found = false;
        }
        $scope.reset_search()

        $scope.search = function(){

            if($scope.query.length){
                ngProgressLite.set(0);
                ngProgressLite.start();

                $scope.reset_search();

                $http.get('/ipc/portal/search/' + $scope.query + '/').then(
                    function(data){
                        ngProgressLite.done();
                        if(data.data){
                            $scope.patient = data.data;
                        }else{
                            $scope.patient_not_found = true;
                        }
                    },
                    function(){
                        ngProgressLite.done();
                    }
                )
            }
        }
    }
);
