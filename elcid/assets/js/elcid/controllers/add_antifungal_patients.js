angular.module('opal.controllers').controller("AddAntifungalPatients", function($scope, DemographicsSearch){
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

  var patient = {
    state: $scope.states.EDITING,
    error: false,
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
    return _.uniq(_.compact(_.flatten(splitted)));
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

  $scope.lookup = function(patientForm){
    /*
    * Query and handle the response of looking up
    * the hospital number for a patient Form.
    */
    if(!patientForm.demographics.hospital_number){
      return
    }
    patientForm.error = undefined;
    patientForm.state = $scope.states.SEARCHING;
    var args = getSearchArgs(patientForm);
    DemographicsSearch.find(patientForm.demographics.hospital_number, args);
  }

  $scope.research = function(){
    /*
    * Look at all the forms that are in editing state
    * and query them again.
    */
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
    /*
    * We don't let the users save the form if the
    * forms still have errors or if we're
    * querying the upstream.
    */
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