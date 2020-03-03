angular.module('opal.services').factory('KeyInvestigationsLoader', function($q, $http, $window) {
  "use strict";

  var load = function(url, patientId){
    var deferred = $q.defer();
    var patientUrl = url + String(patientId) + "/"
    $http.get(patientUrl).then(function(response) {
        deferred.resolve(response.data);
    }, function() {
      $window.alert('Test summary could not be loaded');
    });
    return deferred.promise;
  };

  return {
    load: load
  };
});
