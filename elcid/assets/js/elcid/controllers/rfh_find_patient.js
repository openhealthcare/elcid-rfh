/*
* Different from the standard find patient in that it copies over
* the demographics and location from what is found on the server.
* it also makes sure that you save to last episode that was created
* becuase it assumes episodes are never ended.
*/

angular.module('opal.controllers').controller('RfhFindPatientCtrl',
  function(scope, Episode, Patient, step, episode, $window) {
    "use strict";

    scope.lookup_hospital_number = function() {
        Episode.findByHospitalNumber(
            scope.demographics.hospital_number,
            {
                newPatient:    scope.new_patient,
                newForPatient: scope.new_for_patient,
                error        : function(){
                    // this shouldn't happen, but we should probably handle it better
                    $window.alert('ERROR: More than one patient found with hospital number');
                }
            });
    };

    this.initialise = function(scope){
      scope.state = 'initial';

      scope.demographics = {
        hospital_number: undefined
      };
    };

    scope.new_patient = function(result){
        scope.state = 'editing_demographics';
        scope.$parent.editing.demographics = scope.demographics;
    };

    scope.new_for_patient = function(rawPatient){
        var patient = new Patient(rawPatient);
        scope.demographics = patient.demographics[0].makeCopy();
        scope.state   = 'has_demographics';

        if(patient.episodes.length){
          /*
          * episode are not closed, so just take the last one
          */

          var episode = _.last(patient.episodes);
          var location = _.last(episode.location);

          if(location){
            // the patient already exists
            // copy the location onto the scope for use
            // by the location form
            scope.$parent.editing.location = location.makeCopy();
          }

          scope.$parent.editing.demographics = scope.demographics;
          scope.pathway.save_url = scope.pathway.save_url + "/" + patient.id + "/" + episode.id;
        }
    };
    scope.showNext = function(editing){
        return scope.state === 'has_demographics' || scope.state === 'editing_demographics';
    };

    this.initialise(scope);
});
