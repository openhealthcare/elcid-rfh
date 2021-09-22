angular.module('opal.controllers').controller('RfhFindPatientCtrl',
  function(scope, toMomentFilter, $q, ngProgressLite, $http) {
    "use strict";

    var self = this;

    scope.states = {
      // the initial state the asks for a search term
      INITIAL: "INITIAL",

      // shows the list of patients or suggests the user creates a patient
      // if they click on a patient that already exists, they get taken
      // that patients detail screen
      PATIENT_LIST: "PATIENT_LIST",

      // the user did not want any of the list of patients
      // and is entering demographics manually
      EDITING_DEMOGRAPHICS: "EDITING_DEMOGRAPHICS",
    }

    scope.pollTask = function(taskId){
      /*
      * If we're searching upstream a task ID is returned by the demographics
      * search url. Poll it to wait for the task to complete and then update
      * accordingly.
      */
      var url = '/elcid/v0.1/upstream_demographics_search/' + taskId + '/'
      var deferred = $q.defer();
      var interval = setInterval(function(){
        $http.get(url).then(function(response){
          if(response.data.state === 'SUCCESS'){
            deferred.resolve(response.data.patient_list);
            clearInterval(interval);
          }
          if(response.data.state === 'FAILURE'){
            deferred.reject();
            clearInterval(interval);
          }
        });
      }, 500);
      return deferred.promise;
    }

    scope.getSearch = function(){
      /*
      * Searches upstream, if it returns a task ID, then
      * we are searching upstream so we pass through to
      * the pollTask which will poll the celery task until
      * we're done.
      *
      * The promise this function returns flattens this.
      */
      var url = '/elcid/v0.1/demographics_search/?';
      var deferred = $q.defer();
      var patientURL = url + $.param(scope.searchQuery);
      $http.get(patientURL).then(function(response) {
        if(response.data.task_id){
          scope.pollTask(response.data.task_id).then(function(patientList){
            deferred.resolve(patientList);
          })
        }
        else{
          deferred.resolve(response.data.patient_list);
        }
      }, function(){
        deferred.reject();
      });

      return deferred.promise;
    }

    scope.search = function(){
      ngProgressLite.set(0);
      ngProgressLite.start();
      scope.searchButtonDisabled = true;
      scope.searching = true;
      scope.hideFooter = false;
      scope.getSearch().then(function(patientList){
        scope.patientList = patientList;
        ngProgressLite.done();
        scope.searchButtonDisabled = false;
        scope.searching = false
        if(scope.patientList.length){
          scope.state = scope.states.PATIENT_LIST;
        }
        else{
          if(scope.searchQuery.surname){
            scope.editing.demographics = {
              surname: scope.searchQuery.surname,
              date_of_birth: scope.searchQuery.date_of_birth
            }
          }
        scope.state = scope.states.EDITING_DEMOGRAPHICS
        }
      }, function(){
        alert('Unable to search, please refresh your page and try again.')
      });
    }

    scope.setDate = function(){
      /*
      * validates scope.dateOfBirthString is of the correct
      * format and is a realistic dob.
      *
      * If it is sets it on scope.searchQuery.date_of_birth
      */
      scope.dateError = "";
      scope.searchQuery.date_of_birth = null;
      if(!scope.dateOfBirthString){
        return;
      }
      if(scope.dateOfBirthString.length < 10){
        return;
      }

      // If its not valid, set the error and return
      var mom = moment(scope.dateOfBirthString, "DD/MM/YYYY")
      if(!mom.isValid()){
        scope.dateError = "Please enter a valid date";
        return
      }

      // If its in the future, set the error and return
      var asDate = mom.toDate();
      if(asDate > new Date()){
        scope.dateError = "Please enter a valid date";
        return;
      }

      // if its over a 150 years old, set the error and return
      var ages_ago = new Date()
      ages_ago.setFullYear(new Date().getFullYear() - 150);
      if(asDate < ages_ago){
        scope.dateError = "Please enter a valid date";
        return;
      }
      scope.searchQuery.date_of_birth = scope.dateOfBirthString;
    }

    scope.disableSearchButton = function(){
      if(scope.searchQuery.surname && scope.searchQuery.date_of_birth){
        scope.searchButtonDisabled = false;
        return;
      }
      if(scope.searchQuery.number){
        scope.searchButtonDisabled = false;
        return;
      }
      scope.searchButtonDisabled = true;
    }

    this.resetPathwayMethods = function(){
      /*
      * We are doing a wizard step inside a
      * wizard step.
      *
      * Wrap the pathway previous/next methods
      * to make it look like this is a vanilla
      * wizard pathway.
      */
     scope.pathway.oldHasPrevious = scope.pathway.hasPrevious
     scope.pathway.oldGoPrevious = scope.pathway.goPrevious
     scope.pathway.oldShowNext = scope.pathway.showNext

     var newHasPrevious = function(){
       if(this.currentStep.scope.state){
         if(this.currentStep.scope.state === this.currentStep.scope.states.PATIENT_LIST || scope.state === scope.states.EDITING_DEMOGRAPHICS){
           return true
         }
       }
       return this.oldHasPrevious()
     }
     var newGoPrevious = function(editing){
      if(this.currentStep.scope.state){
        if(this.currentStep.scope.state === this.currentStep.scope.states.PATIENT_LIST || scope.states.EDITING_DEMOGRAPHICS){
          this.currentStep.scope.reset();
          return;
        }
      }
      return this.oldGoPrevious(editing)
     }
     var newShowNext = function(editing){
      if(this.currentStep.scope.state){
        if(this.currentStep.scope.state !== this.currentStep.scope.states.EDITING_DEMOGRAPHICS){
          return false;
        }
      }
      return this.oldShowNext(editing);
     }

     scope.pathway.hasPrevious = _.bind(newHasPrevious, scope.pathway);
     scope.pathway.goPrevious = _.bind(newGoPrevious, scope.pathway);
     scope.pathway.showNext = _.bind(newShowNext, scope.pathway);
    }

    scope.reset = function(){
      scope.state = scope.states.INITIAL;
      scope.searching = false;
      scope.editing.demographics = {};
      scope.areYouSure = false;
      scope.searchButtonDisabled = true;
      scope.dateOfBirthString = "";
      scope.$watch("searchQuery", function(){
        scope.disableSearchButton();
      }, true);
      scope.patientList = [];
      scope.hideFooter = true;
      scope.searchQuery = {
        query: undefined
      };
    }

    this.initialise = function(scope){
      self.resetPathwayMethods();
      scope.reset()
    };

    scope.select = function(demographicsDict){
      scope.editing.demographics = demographicsDict;
      scope.editing.demographics.date_of_birth = toMomentFilter(
        demographicsDict.date_of_birth
      ).toDate();
      scope.pathway.goNext(scope.editing);
    }

    scope.check = function(){
      // if there is only one patient in the patient list
      // and they have a patient id
      // add a required confirmation before they can
      // add a new patient
      if(scope.patientList.length === 1){
        if(scope.patientList[0].patient_id){
          scope.areYouSure = true;
          return;
        }
      }
      scope.state = scope.states.EDITING_DEMOGRAPHICS;
    }

    scope.goToEditing = function(){
      scope.state = scope.states.EDITING_DEMOGRAPHICS;
    }

    scope.showNext = function(editing){
        return scope.state === scope.states.EDITING_DEMOGRAPHICS
    };

    this.initialise(scope);
});
