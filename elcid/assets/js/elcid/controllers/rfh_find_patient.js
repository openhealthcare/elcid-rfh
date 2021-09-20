angular.module('opal.controllers').controller('RfhFindPatientCtrl',
  function(scope, step, episode, DemographicsSearch, $q, ngProgressLite, $http) {
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

    scope.search = function(){
      ngProgressLite.set(0);
      ngProgressLite.start();
      var url = '/elcid/v0.1/demographics_search/?';
      var params = {}
      _.each(scope.searchQuery, function(val, key){
        if(moment.isMoment(val)){
          val = val.format('DD/MM/YYYY');
        }
        params[key] = val;
      });
      var patientURL = url + $.param(params);
      $http.get(patientURL).then(function(response) {
        scope.patientList = response.data.patient_list
        ngProgressLite.done();
        if(scope.patientList.length){
          scope.state = scope.states.PATIENT_LIST
        }
        else{
          scope.state = scope.states.EDITING_DEMOGRAPHICS
        }
      }, function(){
        alert('Unable to search');
        ngProgressLite.done();
      });
    }

    this.initialise = function(scope){
      scope.state = scope.states.INITIAL;
      scope.patientList = [];
      scope.hideFooter = true;
      scope.searchQuery = {
        query: undefined
      };
    };

    this.select = function(demographicsDict){
      scope.demographics = demographicsDict;
      scope.pathway.goNext(scope.editing)
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
