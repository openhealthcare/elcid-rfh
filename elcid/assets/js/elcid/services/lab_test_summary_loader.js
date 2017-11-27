angular.module('opal.services').factory('LabTestSummaryLoader', function($q, $http, $window, $log) {

    "use strict";

    var url = '/labtest/v0.1/lab_test_summary_api/';

    var load = function(patientId){
      var deferred = $q.defer();
      var patientUrl = url + '' + patientId + '/';
      $http({ cache: true, url: patientUrl, method: 'GET'}).then(function(response) {
          deferred.resolve(response.data);
      }, function() {
        $window.alert('Lab test summary could not be loaded');
      });
      return deferred.promise;
    };

    return {
      load: load
    };
});
