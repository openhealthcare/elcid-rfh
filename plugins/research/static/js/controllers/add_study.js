angular.module('opal.controllers').controller('AddStudyCtrl', function(
    $scope, $window, $http, $q, ngProgressLite
){
    "use strict";

    var url = '/api/v0.1/researchstudy/';

    $scope.name = null;

    $scope.create_study = function(){
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http.post(url, { name: $scope.name }).then(
            function(response){
                $window.location = response.data.url;
            },
            function(){
                ngProgressLite.done();
                $window.alert('Error: Could not add study');
            }

        );
    }

});
