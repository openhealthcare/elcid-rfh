angular.module('opal.controllers').controller(
  'GeneralDeleteCtrl',
  function($scope, $modalInstance, item) {
    $scope.destroy = function() {
      item.delete().then(function() {
        $modalInstance.close('deleted');
      });
    };

    $scope.cancel = function() {
      $modalInstance.close('cancel');
    };
  }
);
