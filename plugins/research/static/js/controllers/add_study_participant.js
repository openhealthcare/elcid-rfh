angular.module('opal.controllers').controller('AddStudyParticipantCtrl', function(
    $scope, $window, $http, $q, $routeParams, ngProgressLite
){
    "use strict";

    var add_url    = '/api/v0.1/researchstudy-add-participant/';
    var search_url = '/api/v0.1/researchstudy-search-mrns/';

    $scope.study_id = $routeParams.study_id;
    $scope.mrns     = null;
    $scope.patients = [];
    $scope.missing  = [];
    $scope.matches  = null;

    $scope.search_mrns = function(){
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http.post(search_url, { mrns: $scope.mrns }).then(
            function(response){
                ngProgressLite.done();
                $scope.patients = response.data.patients;
                $scope.missing  = response.data.missing;
                $scope.matches  = response.data.matches
            },
            function(){
                ngProgressLite.done();
                $window.alert('Error: Unexpected issue searching for MRNs');
            }

        );
    }

    $scope.add_patients = function(){
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http.post(add_url, {
            mrns: $scope.matches,
            study_id: $scope.study_id
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


});
