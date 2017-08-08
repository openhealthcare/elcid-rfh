directives.directive("bloodCultureResultDisplay", function(BloodCultureLoader){
  return {
    restrict: 'A',
    scope: true,
    link : function($scope, $element){
      $scope.culture_order = [];
      $scope.cultures = {}
      $scope.loadBloodCultures = function(){
        BloodCultureLoader.load($scope.patient.id).then(function(bc_results){
          $scope.culture_order = bc_results.culture_order;
          $scope.cultures = bc_results.cultures;
        });
      }
      $scope.refreshBloodCultures = function(){
        // we need to refresh the parent so that
        // we consistency tokens get updated for
        // form updates
        $scope.refresh();
        $scope.loadBloodCultures();
      };

      $scope.loadBloodCultures();
    }
  };
});
