angular.module('opal.services').factory('LabTestSummaryLoader', function($q, $http, $window, $log) {

    "use strict";

    var url = '/labtest/v0.1/infection_service_summary_api/';

    var load = function(patientId){
      var deferred = $q.defer();
      var patientUrl = url + '' + patientId + '/';
      $http({ cache: true, url: patientUrl, method: 'GET'}).then(function(response) {
          deferred.resolve(response.data);
      }, function() {
          console.error("unable to load in the infection_service_summary_api");
      });
      return deferred.promise;
    };

    return {
      load: load
    };
});
