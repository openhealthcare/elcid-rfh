angular.module('opal.services').factory('BloodCultureLoader', function($q, $http, $window, $log) {
    "use strict";

    var url = '/elcid/v0.1/blood_culture_results/';

    var load = function(patientId){
      var deferred = $q.defer();
      var patientUrl = url + patientId + "/"
      $http.get(patientUrl).then(function(response) {
          deferred.resolve(response.data);
      }, function() {
        // handle error better
        $window.alert('BloodCultureData could not be loaded');
      });
      return deferred.promise;
    };

    return {
      load: load
    };
});
