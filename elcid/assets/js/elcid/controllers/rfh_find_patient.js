angular.module('opal.controllers').controller('RfhFindPatientCtrl',
  function(scope, step, episode, DemographicsSearch, $window) {
    "use strict";

    scope.lookup_hospital_number = function() {
      DemographicsSearch.find(
        scope.demographics.hospital_number,
        {
            // we can't find the patient on either elicd or the hospital demographcis
            patient_not_found:    scope.new_patient,
            // the patient has been entered into elcid before
            patient_found_in_elcid: scope.new_for_patient,
            // the patient exists on the intrahospital api, but not in elcid
            patient_found_upstream: scope.new_for_patient
        });
    };

    this.initialise = function(scope){
      scope.state = 'initial';
      scope.hideFooter = true;

      scope.demographics = {
        hospital_number: undefined
      };
    };

    scope.new_patient = function(result){
        scope.hideFooter = false;
        scope.state = 'editing_demographics';
    };

    scope.new_for_patient = function(patient){
        var allTags = [];
        _.each(patient.episodes, function(episode){
          _.each(_.keys(episode.tagging[0]), function(tag){
            // episodes are singletons
            // if there is already an episode of this type
            // hoist location and tagging up so
            // it appears in other forms.
            if(step.category_name === episode.category_name){
              scope.editing.tagging = episode.tagging[0];
              scope.editing.location = episode.location[0];
              if(scope.metadata.tags[tag]){
                allTags.push(tag);
              }
            }
          });
        });
        scope.allTags = _.uniq(allTags);
        scope.demographics = patient.demographics[0];
        scope.state   = 'has_demographics';
        scope.hideFooter = false;
    };
    scope.showNext = function(editing){
        return scope.state === 'has_demographics' || scope.state === 'editing_demographics';
    };

    scope.preSave = function(editing){
        // this is not great
        editing.demographics = scope.demographics;
        if(editing.demographics && editing.demographics.patient_id){
          scope.pathway.save_url = scope.pathway.save_url + "/" + editing.demographics.patient_id;
        }
    };

    this.initialise(scope);
});
