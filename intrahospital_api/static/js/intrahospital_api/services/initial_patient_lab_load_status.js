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
  var SUCCESS = "success";
  var FAILURE = "failure";
  var RUNNING = "running";

  var getFromUrl = function(someId, deferred){
    $http.get("/api/v0.1/initial_patient_load/" + lastTestLoad.id + "/").then(
      function(initialPatientLoad){
        debugger;
        if(initialPatientLoad.state===SUCCESS){
          deferred.resolve(SUCCESS);
        }
        else if(initialPatientLoad.state!==RUNNING){
          $timeout(function() { getFromUrl(someId); }, 0, false);
        }
        else{
          deferred.reject(FAILURE);
        }
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
      if(!episode.initial_patient_load.length){
        // the patient has no test load
        return null;
      }
      var lastTestLoad = episode.initial_patient_load;

      if(_.last(lastTestLoad).state === SUCCESS){
        deferred.resolve(SUCCESS);
      }
      else{
        getFromUrl(lastTestLoad.id, deferred);
      }
      return deferred.promise;
    },
    SUCCESS: SUCCESS,
    FAILURE: FAILURE,
    RUNNING: RUNNING
  }

});
