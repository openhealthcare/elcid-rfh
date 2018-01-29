describe('ProcedureFormCtrl', function() {
  "use strict";
  var mkController, $scope, $controller;

  beforeEach(function(){

    module('opal.controllers');
    inject(function($injector){
      var $rootScope   = $injector.get('$rootScope');
      $scope       = $rootScope.$new();
      $controller  = $injector.get('$controller');
    });

    mkController = function(){
        var ctrl = $controller('ProcedureFormCtrl', {
            $scope: $scope,
        });
        return ctrl;
    };
    $scope.procedure = {
      surgical_procedure: undefined, medical_procedure: undefined
    };
  });

  it('should remember previous results', function(){
    $scope.procedure = {surgical_procedure: "heart bypass"};
    var ctrl = mkController();
    expect(ctrl.selectedProcedure).toBe("heart bypass");
  });

  it('should save to the medical list', function(){
    $scope.medicalprocedure_list = ["heart bypass"];
    var ctrl = mkController();
    ctrl.selectedProcedure = "heart bypass"
    $scope.$apply();
    expect($scope.procedure.medical_procedure).toBe("heart bypass");
    expect($scope.procedure.surgical_procedure).toBe(undefined);
  });

  it('should save to the surgical list', function(){
    $scope.surgicalprocedure_list = ["heart bypass"];
    var ctrl = mkController();
    ctrl.selectedProcedure = "heart bypass"
    $scope.$apply();
    expect($scope.procedure.surgical_procedure).toBe("heart bypass");
    expect($scope.procedure.medical_procedure).toBe(undefined);
  });

  it('should nuke if none necessary', function(){
    $scope.procedure = {surgical_procedure: "heart bypass"};
    var ctrl = mkController();
    ctrl.selectedProcedure = ""
    $scope.$apply();
    expect($scope.procedure.surgical_procedure).toBe(undefined);
    expect($scope.procedure.medical_procedure).toBe(undefined);
  });
});
