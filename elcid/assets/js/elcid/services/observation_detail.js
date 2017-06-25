angular.module('opal.services').factory('ObservationDetail', function($q, $http, $window, $log) {

    "use strict";

    var url = '/labtest/v0.1/lab_test_observation_detail/';

    var load = function(patientId, labTestSlug, observationSlug){
      var deferred = $q.defer();
      var params = $.param({
        observation: observationSlug,
        labtest: labTestSlug
      })
      var specificUrl = url + patientId  + "/?" + params;
      $http({ cache: true, url: specificUrl, method: 'GET'}).then(function(response) {
          deferred.resolve(response.data);
      }, function() {
        // handle error better
        $window.alert('Observation data could not be loaded');
      });
      return deferred.promise;
    };

    return {
      load: load
    };
});
