angular.module('opal.controllers').controller('BloodCultureFormCtrl',
function($scope, $cookieStore, $timeout,
                         $modalInstance, $modal, $q,
                         ngProgressLite, $controller,
                         profile, item, options, episode) {
      "use strict";

      var parentCtrl = $controller("EditItemCtrl", {
          $scope: $scope,
          $modalInstance: $modalInstance,
          episode: episode,
          options: options,
          item: item,
          profile: profile
      });
      var vm = this;

      _.extend(vm, parentCtrl);

      $scope.addAerobic = function(){
        $scope.aerobic_models.push({
          aerobic: true
        });
      };

      $scope.addAnaerobic = function(){
        $scope.anaerobic_models.push({
          aerobic: false
        });
      };

      $scope.deleteAnaerobic = function(index){
        $scope.anaerobic_models.splice(index, 1);
      }

      $scope.deleteAerobic = function(index){
        $scope.aerobic_models.splice(index, 1);
      }

      $scope.aerobic_models = angular.copy(_.filter(item.isolates, function(x){
        return x.aerobic
      }));
      $scope.anaerobic_models = angular.copy(_.filter(item.isolates, function(x){
        return !x.aerobic
      }));

      $scope.preSave = function(editing){
        // filter out completely empty fields
        var toUpdate = $scope.aerobic_models.concat($scope.anaerobic_models);

        var nonEmpties = _.reject(toUpdate, function(x){
            return _.isEmpty(_.omit(x, "aerobic"));
        });

        editing.blood_culture.isolates = nonEmpties;
    };
});
