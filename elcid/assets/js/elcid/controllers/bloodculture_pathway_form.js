angular.module('opal.controllers').controller('BloodCulturePathwayFormCtrl',
function($modal, $q, ngProgressLite, scope, step, episode, BloodCultureHelper) {
      "use strict";

      if(episode && episode.tagging.length){
        scope.editing.tagging = episode.tagging[0].makeCopy();
      }
      else{
        scope.editing.tagging = {};
      }
      if(!scope.editing.lab_test){
        scope.editing.lab_test = [];
      }
      scope.bloodCultureHelper = new BloodCultureHelper(scope.editing.lab_test);

      scope.preSave = function(editing){
        scope.bloodCultureHelper.preSave(editing);
      }

      // scope.initialise = function(bloodCultures){
      //     _.each(bloodCultures, function(bloodCulture){
      //       bloodCulture._formHelper = new BloodCultureFormHelper(
      //         bloodCulture, scope.metadata
      //       );
      //     });
      // };
      //
      // if(_.isUndefined(scope.editing.blood_culture)){
      //   scope.editing.blood_culture = [{}];
      // }
      // else if(!_.isArray(scope.editing.blood_culture)){
      //   scope.editing.blood_culture = [scope.editing.blood_culture];
      // }
      //
      // scope.addBloodCulture = function(){
      //   var newBloodCulture = {};
      //   newBloodCulture._formHelper = new BloodCultureFormHelper(newBloodCulture);
      //   scope.editing.blood_culture.push(newBloodCulture);
      // };
      //
      // scope.preSave = function(editing){
      //   _.each(editing.blood_culture, function(bc){
      //     _.each(bc.isolates, function(i){
      //       delete i._formHelper;
      //     })
      //     delete bc._formHelper;
      //   });
      // };
      //
      // scope.initialise(scope.editing.blood_culture);
});
