angular.module('opal.controllers').controller("AddAntifungalPatients", function($scope, DemographicsSearch){
  "use strict";

  $scope.patientForms = [];

  $scope.states = {
    EDITING: "editing",
    SEARCHING: "searching",
    FOUND: "found",
    ERROR: "error"
  }

  $scope.stages = {
    LOOKUP_PATIENTS: "lookup_patients",
    ADD_PATIENTS: "add_patients"
  }

  var patient = {
    state: $scope.states.EDITING,
    demographics: {
      hospital_number: undefined,
      // if populated from the server this has the rest of demographcis.to_dict()
    },
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
    var columnHeader = "patient_hospitalno";
    var nums =  _.uniq(_.compact(_.flatten(splitted)));
    return _.without(nums, columnHeader);
  }


  $scope.lookupAll = function(){
    $scope.stage = $scope.stages.ADD_PATIENTS;
    var hns = $scope.flattenAndClean($scope.editing.hospitalNumbers);
    $scope.patientForms = _.map(hns, newPatientFromHospitalNumer);
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

  $scope.getSearchArgs = function(patientForm){
    var searchArgs = {}

    var patientFound = function(result){
      patientForm.demographics = result.demographics[0];
      patientForm.state = $scope.states.FOUND;
    }
    var patientNotFound = function(){
      patientForm.state = $scope.states.ERROR;
    }

    searchArgs[DemographicsSearch.PATIENT_FOUND_IN_ELCID] = patientFound;
    searchArgs[DemographicsSearch.PATIENT_FOUND_UPSTREAM] = patientFound;
    searchArgs[DemographicsSearch.PATIENT_NOT_FOUND] = patientNotFound;
    return searchArgs;
  }


  $scope.getDemographicsJson = function(){
    return JSON.stringify(_.pluck($scope.patientForms, "demographics"));
  }

  var lookup = function(patientForm){
    if(!patientForm.demographics.hospital_number || !patientForm.demographics.hospital_number.length){
      return
    }
    patientForm.state = $scope.states.SEARCHING;
    var args = $scope.getSearchArgs(patientForm);
    DemographicsSearch.find(patientForm.demographics.hospital_number, args);
  }

  $scope.lookup = lookup;

  var lookupDebounced = _.debounce(lookup, 500);

  $scope.lookupDebounced = function(patientForm){
    /*
    * Query and handle the response of looking up
    * the hospital number for a patient Form.
    */
    lookupDebounced(patientForm);
    // var args = $scope.getSearchArgs(patientForm);
    // DemographicsSearch.find(patientForm.demographics.hospital_number, args);
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
    /*
    * We don't let the users save the form if the
    * forms still have errors or if we're
    * querying the upstream.
    */
    return _.all($scope.patientForms, function(patientForm){
      return patientForm.state === $scope.states.FOUND;
    });
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