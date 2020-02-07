angular.module('opal.controllers').controller("AddPatients", function($scope, DemographicsSearch){
  "use strict";

  $scope.patientForms = [];

  $scope.states = {
    EDITING: "editing",
    SEARCHING: "searching",
    FOUND: "found"
  }

  $scope.stages = {
    LOOKUP_PATIENTS: "lookup_patients",
    ADD_PATIENTS: "add_patients"
  }

  $scope.flattenAndClean = function(hospitalNumbers){
    /*
    * takes in a string of hospital numbers seperated by
    * new line, spaces and or commas.
    *
    * returns an an array of hospital numbers
    */
    var splitted = _.map(hospitalNumbers.split(" "), function(x){
      return _.map(x.split(","), function(y){
        return _.map(y.split("\n"))
      })
    })
    return _.uniq(_.compact(_.flatten(splitted)));
  }


  $scope.lookupAll = function(){
    $scope.stage = $scope.stages.ADD_PATIENTS;
    var hns = $scope.flattenAndClean($scope.editing.hospitalNumbers);
    $scope.patientForms = _.map(hns, newPatientFromHospitalNumer);
  }

  var patient = {
    state: $scope.states.FOUND,
    error: false,
    demographics: {
      hospital_number: undefined,
      // if populated from the server this has the rest of demographcis.to_dict()
    },
  }

  var newPatientFromHospitalNumer = function(hospitalNumber){
    /*
    * Return a new patientForm and start the search
    */
   var newPatient = _.clone(patient);
   newPatient.demographics = {hospital_number: hospitalNumber};
   $scope.lookup(newPatient);
   return newPatient;
  }

  var getSearchArgs = function(patient){
    var searchArgs = {}
    searchArgs[DemographicsSearch.PATIENT_FOUND_IN_ELCID] = function(result){
      patient.demographics = result.demographics[0];
      patient.state = $scope.states.FOUND;
      patient.error = false;
    }
    searchArgs[DemographicsSearch.PATIENT_FOUND_UPSTREAM] = function(result){
      patient.demographics = result.demographics[0];
      patient.state = $scope.states.FOUND;
      patient.error = false;
    }
    searchArgs[DemographicsSearch.PATIENT_NOT_FOUND] = function(){
      patient.state = $scope.states.EDITING;
      patient.error = true;
    }

    return searchArgs;
  }


  $scope.get_demographics_json = function(){
    return JSON.stringify(_.pluck($scope.patientForms, "demographics"));
  }

  $scope.lookup = function(p){
    if(!p.demographics.hospital_number){
      return
    }
    p.error = undefined;
    p.state = $scope.states.SEARCHING;
    var args = getSearchArgs(p)
    DemographicsSearch.find(p.demographics.hospital_number, args);
  }

  $scope.research = function(){
    _.each($scope.patientForms, function(pf){
      if(pf.state === $scope.states.EDITING && !pf.error){
        $scope.lookup(pf);
      }
    });
  }

  $scope.filterForms = function(filterArgs){
    /*
    * runs _.where on forms so if you pass in
    * {state: "editing"} it will return all
    * forms where state === "editing"
    */
    return _.where($scope.patientForms, filterArgs);
  }

  $scope.canSave = function(){
    var hasSearch = $scope.filterForms({state: $scope.states.SEARCHING});
    var hasErrors = $scope.filterForms({error: true});
    return !hasSearch.length && !hasErrors.length
  }

  $scope.remove = function(idx){
    $scope.patientForms.splice(idx, 1);
    if(!$scope.patientForms.length){
      $scope.stage = $scope.stages.LOOKUP_PATIENTS;
    }
  }

  $scope.init = function(){
    $scope.stage = $scope.stages.LOOKUP_PATIENTS;
    $scope.editing = {
      hospitalNumbers: ""
    }
  }

  $scope.init();
});
