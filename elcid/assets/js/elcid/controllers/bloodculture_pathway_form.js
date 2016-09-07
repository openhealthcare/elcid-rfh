angular.module('opal.controllers').controller('BloodCulturePathwayFormCtrl',
function( $modal, $q, ngProgressLite, scope, step, episode) {
      "use strict";

      scope.step = step;

      scope.addAerobic = function(){
        scope.aerobicModels.push({
          aerobic: true
        });
      };

      scope.addAnaerobic = function(){
        scope.anaerobicModels.push({
          aerobic: false
        });
      };

      scope.deleteAnaerobic = function(index){
        scope.anaerobicModels.splice(index, 1);
      }

      scope.deleteAerobic = function(index){
        scope.aerobicModels.splice(index, 1);
      }

      scope.preSave = function(editing){
        // filter out completely empty fields
        if(!editing.blood_culture && scope.aerobicModels.length && scope.anaerobicModels.length){
          editing.blood_culture = [{}];
        }
        var toUpdate = scope.aerobicModels.concat(scope.anaerobicModels);

        var nonEmpties = _.reject(toUpdate, function(x){
            return _.isEmpty(_.omit(x, "aerobic"));
        });

        editing.blood_culture.isolates = nonEmpties;
      }

      scope.initialise = function(item){
          var isolates = item.isolates || [];
          scope.aerobicModels = angular.copy(_.filter(isolates, function(x){
            return x.aerobic
          }));
          scope.anaerobicModels = angular.copy(_.filter(isolates, function(x){
            return !x.aerobic
          }));
      }

      if(scope.editing.blood_culture){
          scope.initialise(scope.editing.blood_culture);
      }
      else{
          scope.initialise({});
      }
});
