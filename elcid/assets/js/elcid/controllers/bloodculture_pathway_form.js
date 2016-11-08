angular.module('opal.controllers').controller('BloodCulturePathwayFormCtrl',
function( $modal, $q, ngProgressLite, scope, step, episode, BloodCultureFormHelper) {
      "use strict";

      scope.initialise = function(bloodCultures){
          _.each(bloodCultures, function(bloodCulture){
            bloodCulture._formHelper = new BloodCultureFormHelper(
              bloodCulture, scope.metadata
            );
          });
      };

      if(_.isUndefined(scope.editing.blood_culture)){
        scope.editing.blood_culture = [{}];
      }
      else if(!_.isArray(scope.editing.blood_culture)){
        scope.editing.blood_culture = [scope.editing.blood_culture];
      }

      scope.addBloodCulture = function(){
        var newBloodCulture = {};
        newBloodCulture._formHelper = new BloodCultureFormHelper(newBloodCulture);
        scope.editing.blood_culture.push(newBloodCulture);
      };

      scope.preSave = function(editing){
        _.each(editing.blood_culture, function(bc){
          _.each(bc.isolates, function(i){
            delete i._formHelper;
          })
          delete bc._formHelper;
        });
      };

      scope.initialise(scope.editing.blood_culture);
});
