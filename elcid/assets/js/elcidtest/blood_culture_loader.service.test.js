describe('BloodCultureLoader', function(){
  "use strict";

  var BloodCultureLoader, $rootScope, $httpBackend;
  var culture_order = [["21/10/2000", "12222L21323"]];
  var cultures = {
    "21/10/2000": {
      "12222L21323": {
        aerobic: [{
          lab_test_type: "Gram Stain",
          result: {result: "Yeast"}
        }],
        anaerobic: []
      }
    }
  }

  beforeEach(function(){
    module('opal.services');
    inject(function($injector){
      BloodCultureLoader = $injector.get('BloodCultureLoader');
      $rootScope = $injector.get('$rootScope');
      $httpBackend = $injector.get('$httpBackend');
    });
  });

  it('should fetch data and return a promise', function(){
    $httpBackend.expectGET('/elcid/v0.1/blood_culture_results/52/').respond(
      "some result"
    );
    var result;
    BloodCultureLoader.load(52).then(function(someR){
      result = someR;
    });
    $rootScope.$apply();
    $httpBackend.flush();
    expect(result).toBe("some result");
  });
});
