angular.module('opal.services').factory('LabTestSummaryLoader', function($q, $http) {

    "use strict";

    var load = function(apiUrl){
      var deferred = $q.defer();
      $http({ cache: true, url: apiUrl, method: 'GET'}).then(function(response) {
          deferred.resolve(response.data);
      }, function() {
          console.error("unable to load in the lab_test_summary_api");
      });
      return deferred.promise;
    };

    return {
      load: load
    };
});
