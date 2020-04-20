angular.module('opal.services').factory('TestSummaryLoader', function($q, $http, $window) {
  "use strict";

  var url = '/api/v0.1/tb_test_summary/';

  var load = function(patientId){
    var deferred = $q.defer();
    var patientUrl = url + patientId + "/"
    $http.get(patientUrl).then(function(response) {
        deferred.resolve(response.data);
    }, function() {
      // handle error better
      $window.alert('TB summary could not be loaded');
    });
    return deferred.promise;
  };

  return {
    load: load
  };
});
