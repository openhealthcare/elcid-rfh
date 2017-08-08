directives.directive("bloodCultureResultDisplay", function(BloodCultureLoader){
  return {
    restrict: 'A',
    scope: true,
    link : function($scope, $element){
      $scope.keys = [];
      $scope.cultures = {}
      $scope.refreshBloodCultures = function(){
        BloodCultureLoader.load($scope.patient.id).then(function(bc_results){
          $scope.bc_order = bc_results.bc_order;
          $scope.cultures = bc_results.cultures;
        });
      }

      $scope.refreshBloodCultures();
    }
  };
});
