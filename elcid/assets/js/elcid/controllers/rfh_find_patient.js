angular.module('opal.controllers').controller('RfhFindPatientCtrl',
  function(scope, toMomentFilter, $q, ngProgressLite, $http) {
    "use strict";

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
      var params = {}
      _.each(scope.searchQuery, function(val, key){
        if(moment.isMoment(val)){
          val = val.format('DD/MM/YYYY');
        }
        params[key] = val;
      });
      var patientURL = url + $.param(params);
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
      scope.searching = true
      scope.getSearch().then(function(patientList){
        scope.patientList = patientList;
        ngProgressLite.done();
        scope.searchButtonDisabled = false;
        scope.searching = false
        scope.hideFooter = true;
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
          scope.goToEditing();
        }
      });
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

    this.initialise = function(scope){
      scope.state = scope.states.INITIAL;
      scope.searching = false;
      scope.searchButtonDisabled = true;
      scope.$watch("searchQuery", function(){
        scope.disableSearchButton();
      }, true);
      scope.patientList = [];
      scope.hideFooter = true;
      scope.searchQuery = {
        query: undefined
      };
    };

    scope.select = function(demographicsDict){
      scope.editing.demographics = demographicsDict;
      scope.editing.demographics.date_of_birth = toMomentFilter(
        demographicsDict.date_of_birth
      ).toDate();
      scope.pathway.goNext(scope.editing);
    }

    scope.goToEditing = function(){
      scope.state = scope.states.EDITING_DEMOGRAPHICS
      scope.hideFooter = false;
    }

    scope.showNext = function(editing){
        return scope.state === scope.states.EDITING_DEMOGRAPHICS
    };

    this.initialise(scope);
});
