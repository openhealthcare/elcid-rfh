angular.module('opal.services').factory('UpstreamBloodCultureLoader', function($q, $http, $window) {
    "use strict";

    var url = '/elcid/v0.1/upstream_blood_culture_results/';

    var load = function(patientId){
      var deferred = $q.defer();
      var patientUrl = url + patientId + "/"
      $http.get(patientUrl).then(function(response) {
          deferred.resolve(response.data);
      }, function() {
        // handle error better
        $window.alert('Upstream Blood Culture Data could not be loaded');
      });
      return deferred.promise;
    };

    return {
      load: load
    };
});
