angular.module('opal.controllers').controller(
  'ProcedureFormCtrl', function($scope) {
    "use strict";
    var vm = this;
    vm.editing = {procedure_type: undefined};
    vm.procedureTypes = ["medical", "surgical"];
    vm.procedures = [];
    vm.selectedProcedure = "";

    if(!$scope.editing.procedure){
      $scope.editing.procedure = {};
    }

    vm.procedures = _.union($scope.medicalprocedure_list, $scope.surgicalprocedure_list);

    $scope.$watch(angular.bind(vm, function () {
        return this.selectedProcedure;
    }), function(procedureType){
        if(_.contains($scope.medicalprocedure_list, vm.selectedProcedure)){
            $scope.editing.procedure.medical_procedure = vm.selectedProcedure;
            $scope.editing.procedure.surgical_procedure = undefined;
        }
        else if(_.contains($scope.surgicalprocedure_list, vm.selectedProcedure)){
            $scope.editing.procedure.surgical_procedure = vm.selectedProcedure;
            $scope.editing.procedure.medical_procedure = undefined;
        }
    });
});
