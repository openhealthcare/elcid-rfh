angular.module('opal.controllers').controller('RfhFindPatientCtrl',
  function(scope, step, episode, DemographicsSearch, ngProgressLite, $window) {
    "use strict";

    scope.lookup_hospital_number = function() {
      ngProgressLite.set(0);
      ngProgressLite.start();
      var searchArgs = {}
      // we can't find the patient on either elicd or the hospital demographics
      searchArgs[DemographicsSearch.PATIENT_FOUND_IN_ELCID] = scope.new_for_patient;

      // the patient has been entered into elcid before
      searchArgs[DemographicsSearch.PATIENT_FOUND_UPSTREAM] = scope.new_for_patient;

      // the patient exists on the intrahospital api, but not in elcid
      searchArgs[DemographicsSearch.PATIENT_NOT_FOUND] = scope.new_patient;

      DemographicsSearch.find(
        scope.demographics.hospital_number,
        searchArgs
      )
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
        ngProgressLite.done();
    };

    scope.new_for_patient = function(patient){
        var allTags = [];
        _.each(patient.episodes, function(episode){
          _.each(_.keys(episode.tagging[0]), function(tag){
            if(scope.metadata.tags[tag]){
              allTags.push(tag);
            }
          });
        });
        scope.allTags = _.uniq(allTags);
        scope.demographics = patient.demographics[0];
        scope.state   = 'has_demographics';
        scope.hideFooter = false;
        ngProgressLite.done();
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
