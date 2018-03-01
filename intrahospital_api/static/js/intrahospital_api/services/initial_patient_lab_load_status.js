angular.module('opal.services').service('InitialPatientTestLoadStatus', function($q, $http){
  "use strict";
  /*
  * returns a promise or null.
  * if its null this patient has not been reconciled, so no patient
  * load status exists for them.
  * the promise is waiting while the are waiting
  * the promise is successful when its successful
  * the promise fails, when it, erm fails...
  */
  var url = ""
  var SUCCESS = "success";
  var FAILURE = "failure";
  var RUNNING = "running";

  var getFromUrl(someId){
    $http.get("/api/v0.1/initial_patient_load/" + lastTestLoad.id + "/").then(
      function(initialPatientLoad){
        if(initialPatientLoad.state===SUCCESS){
          deferred.resolve(SUCCESS);
        }
        else if()
      },
      function(error){
        deferred.reject(FAILURE);
      }
    )
  }

  return {
    load: function(episode){
      // can actually be passed a patient or an episode
      var deferred = $q.defer();

      if(!episode.intial_patient_test_load.length){
        // the patient has no test load
        return null;
      }
      var lastTestLoad = episode.intial_patient_test_load;

      if(!_.last(lastTestLoad).state === SUCCESS){
        deferred.resolve(SUCCESS);
      }
      else{
        $http.get("/api/v0.1/initial_patient_load/" + lastTestLoad.id + "/").then(
          function(success){
            deferred.resolve(SUCCESS);
          },
          function(error){
            deferred.reject(FAILURE);
          }
        )
      }

      return deferred.promise;
    },
    SUCCESS: SUCCESS,
    FAILURE: FAILURE,
    RUNNING: RUNNING
  }

});
