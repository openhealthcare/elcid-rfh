directives.directive("bloodCultureResultDisplay", function(BloodCultureLoader){
  return {
    restrict: 'A',
    scope: true,
    link : function($scope, $element){
      $scope.bc_order = [];
      $scope.cultures = {}
      $scope.refreshBloodCultures = function(){
        // we need to refresh the parent so that
        // we consistency tokens get updated for
        // form updates
        $scope.refresh();
        BloodCultureLoader.load($scope.patient.id).then(function(bc_results){
          $scope.bc_order = bc_results.bc_order;
          $scope.cultures = bc_results.cultures;
        });
      }

      $scope.refreshBloodCultures();
    }
  };
});
