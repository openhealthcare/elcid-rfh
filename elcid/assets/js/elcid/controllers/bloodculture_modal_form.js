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

      $scope.aerobic_models = [];
      $scope.anaerobic_models = [];

      $scope.preSave = function(editing){
        // filter out completely empty fields
        var toUpdate = vm.aerobic_models.concat(vm.anaerobic_models);

        var nonEmpties = _.reject(toUpdate, function(x){
            return _.isEmpty(_.omit(x, "aerobic"));
        });

        editing.blood_culture.isolates = nonEmpties;
    };
});
