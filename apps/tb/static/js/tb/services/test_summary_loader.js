angular.module('opal.services').factory('TestSummaryLoader', function($q, $http, $window) {
  "use strict";

  var load = function(url, patientId){
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
