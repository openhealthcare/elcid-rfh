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
  var ABSENT = "absent";
  var LOADING = "loading";

  var InitialPatientTestLoadStatus = function(episode){
    // can actually be passed a patient or an episode
    this.episode = episode;
    this.state = LOADING;
    this.getFromUrl = function(){
      var self = this;
    }
    this.deferred = $q.defer();
  };

  InitialPatientTestLoadStatus.prototype = {
    getFromUrl: function(someId){
      var self = this;
      $http.get("/api/v0.1/initial_patient_load/" + lastTestLoad.id + "/").then(
        function(initialPatientLoad){
          if(initialPatientLoad.state===SUCCESS){
            self.state = SUCCESS;
            self.deferred.resolve(SUCCESS);
          }
          else if(initialPatientLoad.state!==RUNNING){
            $timeout(function() { self.getFromUrl(someId); }, 0, false);
          }
          else{
            self.state = FAILURE;
            self.deferred.reject(FAILURE);
          }
        },
        function(error){
          // TODO: we need to catch a 404 as this would just mean absent
          self.state = FAILURE;
          self.deferred.reject(FAILURE);
        }
      )
    },
    isAbsent: function(){
      return this.state === ABSENT;
    },
    isLoading: function(){
      return this.state === LOADING;
    },
    isLoaded: function(){
      return this.state === SUCCESS;
    },
    isFailed: function(){
      return this.state === FAILURE;
    },
    load: function(){
      if(!this.episode.initial_patient_load.length){
        // the patient has no test load
        this.state = ABSENT;
        return null;
      }
      var lastTestLoad = this.episode.initial_patient_load;

      if(_.last(lastTestLoad).state === SUCCESS){
        this.state = SUCCESS;
        this.deferred.resolve(SUCCESS);
      }
      else{
        this.getFromUrl(lastTestLoad.id);
      }
      this.promise = this.deferred.promise;
    }
  };

  return InitialPatientTestLoadStatus;
});
