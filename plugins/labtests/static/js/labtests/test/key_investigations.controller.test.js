describe('KeyInvestigations', function(){
  "use strict";
  var $rootScope, $scope, $controller, InitialPatientTestLoadStatus, InitialPatientTestLoadStatusConstructor;
  var KeyInvestigationsLoader, $attrs;

  beforeEach(function(){
    module('opal');
  });

  beforeEach(function(){
    inject(function($injector){
      $rootScope = $injector.get('$rootScope');
      $scope = $rootScope.$new();
      $controller = $injector.get('$controller');
    });
    InitialPatientTestLoadStatus = jasmine.createSpyObj(["load", "isAbsent"]);
    InitialPatientTestLoadStatus.promise = {
      then: function(x){x()}
    };
    InitialPatientTestLoadStatusConstructor = jasmine.createSpy().and.returnValue(InitialPatientTestLoadStatus);
    KeyInvestigationsLoader = jasmine.createSpyObj(["load"]);
    KeyInvestigationsLoader.load.and.returnValue({then: function(x){x("someValue")}});
    $scope.episode = {
      demographics: [{
        patient_id: 1
      }]
    }

    $attrs = {
      apiUrl: "/something/"
    }
  });

  it('should hoist results on to the results onto scope if the patient has lab tests', function(){
    InitialPatientTestLoadStatus.isAbsent.and.returnValue(false);
    $controller('KeyInvestigations',  {
      $scope: $scope,
      $attrs: $attrs,
      InitialPatientTestLoadStatus: InitialPatientTestLoadStatusConstructor,
      KeyInvestigationsLoader: KeyInvestigationsLoader,
    });
    expect($scope.data).toEqual("someValue");
  });

  it('should not load lab tests if the patient unit tests are absent', function(){
    InitialPatientTestLoadStatus.isAbsent.and.returnValue(true);
    $controller('KeyInvestigations',  {
      $scope: $scope,
      $attrs: $attrs,
      InitialPatientTestLoadStatus: InitialPatientTestLoadStatusConstructor,
      KeyInvestigationsLoader: KeyInvestigationsLoader,
    });
    expect(KeyInvestigationsLoader.load).not.toHaveBeenCalled();
  });

  it('should host the patient load status onto scope', function(){
    InitialPatientTestLoadStatus.isAbsent.and.returnValue(true);
    $controller('KeyInvestigations',  {
      $scope: $scope,
      $attrs: $attrs,
      InitialPatientTestLoadStatus: InitialPatientTestLoadStatusConstructor,
      KeyInvestigationsLoader: KeyInvestigationsLoader,
    });
    expect($scope.patientLoadStatus).toEqual(InitialPatientTestLoadStatus);
  });
});