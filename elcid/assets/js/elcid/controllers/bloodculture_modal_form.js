angular.module('opal.controllers').controller('BloodCultureFormCtrl',
function(
  $scope, $modalInstance, $modal, $controller,
  profile, item, metadata, referencedata, episode,
  BloodCultureFormHelper
) {
      "use strict";

      var parentCtrl = $controller("EditItemCtrl", {
          $scope: $scope,
          $modalInstance: $modalInstance,
          episode: episode,
          metadata: metadata,
          referencedata: referencedata,
          item: item,
          profile: profile
      });
      var vm = this;
      _.extend(vm, parentCtrl);

      $scope.editing.blood_culture._formHelper = new BloodCultureFormHelper(
        $scope.editing.blood_culture, metadata
      );
      $scope.singleModel = 0;

      $scope.preSave = function(editing){
        _.each(editing.blood_culture.isolates, function(i){
          delete i._formHelper;
        })
        delete editing.blood_culture._formHelper
      };
});
