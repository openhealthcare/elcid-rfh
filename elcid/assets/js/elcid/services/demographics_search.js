angular.module('opal.services').factory('DemographicsSearch', function($http, $window) {
  "use strict";
  /*
  * The demographics search used by the find patient
  * pathway.
  */

  var url = '/elcid/v0.1/demographics_search/?hospital_number=';

  // we have four call backs that we are expecting

  // patient is found in elcid (Yay!)
  var PATIENT_FOUND_IN_ELCID = "patient_found_in_elcid";

  // patient is not found in elcid but is found
  // in the hospital (Yay!)
  var PATIENT_FOUND_UPSTREAM = "patient_found_upstream";

  // patient is not found
  var PATIENT_NOT_FOUND = "patient_not_found";

  var expectedStatuses = [
    PATIENT_FOUND_IN_ELCID,
    PATIENT_FOUND_UPSTREAM,
    PATIENT_NOT_FOUND,
  ]

  var find = function(hospitalNumber, findPatientOptions){
    var callBackNames = _.keys(findPatientOptions);
    _.each(callBackNames, function(key){
      if(expectedStatuses.indexOf(key) === -1){
        throw "unknown call back";
      }
    });
    var patientUrl = url + encodeURIComponent(hospitalNumber)
    $http.get(patientUrl).then(function(response) {
      if(response.data.status == PATIENT_FOUND_IN_ELCID){
        findPatientOptions[PATIENT_FOUND_IN_ELCID](response.data.patient);
      }
      else if(response.data.status == PATIENT_FOUND_UPSTREAM){
        findPatientOptions[PATIENT_FOUND_UPSTREAM](response.data.patient);
      }
      else if(response.data.status == PATIENT_NOT_FOUND){
        findPatientOptions[PATIENT_NOT_FOUND](response.data.patient);
      }
      else{
        $window.alert('DemographicsSearch could not be loaded');
      }
    }, function(){
      $window.alert('DemographicsSearch could not be loaded');
    });
  }

  return {
    find: find,
    PATIENT_FOUND_IN_ELCID: PATIENT_FOUND_IN_ELCID,
    PATIENT_FOUND_UPSTREAM: PATIENT_FOUND_UPSTREAM,
    PATIENT_NOT_FOUND: PATIENT_NOT_FOUND,
  };
});
