angular.module('opal.services').factory('LabTestResults', function($q, $http, $window, $log) {

    "use strict";

    var url = '/labtest/v0.1/lab_test_results_view/';

    var load = function(patientId){
      var deferred = $q.defer();
      var patientUrl = url + '' + patientId + '/';
      $http({ cache: true, url: patientUrl, method: 'GET'}).then(function(response) {
          deferred.resolve(response.data);
      }, function() {
        // handle error better
        $window.alert('Lab test results could not be loaded');
      });
      return deferred.promise;
    };

    return {
      load: load
    };
});
