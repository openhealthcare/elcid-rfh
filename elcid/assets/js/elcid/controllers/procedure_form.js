angular.module('opal.controllers').controller(
  'ProcedureFormCtrl', function($scope) {
    "use strict";
    var vm = this;
    vm.procedureTypes = ["medical", "surgical"];
    vm.procedures = [];
    vm.selectedProcedure = $scope.procedure.surgical_procedure || $scope.procedure.medical_procedure;
    vm.procedures = _.union($scope.medicalprocedure_list, $scope.surgicalprocedure_list);

    $scope.$watch(angular.bind(vm, function () {
        return this.selectedProcedure;
    }), function(procedureType){
        if(_.contains($scope.medicalprocedure_list, vm.selectedProcedure)){
            $scope.procedure.medical_procedure = vm.selectedProcedure;
            $scope.procedure.surgical_procedure = undefined;
        }
        else if(_.contains($scope.surgicalprocedure_list, vm.selectedProcedure)){
            $scope.procedure.surgical_procedure = vm.selectedProcedure;
            $scope.procedure.medical_procedure = undefined;
        }
        else if(!vm.selectedProcedure || !vm.selectedProcedure.length){
            // if its undefined or an empty string, nuke it
            $scope.procedure.surgical_procedure = undefined;
            $scope.procedure.medical_procedure = undefined;
        }
    });
});
