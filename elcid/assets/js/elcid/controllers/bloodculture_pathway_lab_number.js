angular.module('opal.controllers').controller('BloodCultureLabNumberPathwayFormCtrl',
function( $modal, $q, ngProgressLite, scope, step, episode, BloodCultureHelper) {
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
});
