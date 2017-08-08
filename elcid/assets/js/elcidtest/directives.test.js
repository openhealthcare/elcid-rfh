describe('OPAL Directives', function(){
    "use strict";

    var $compile, BloodCultureLoader, scope, $rootScope, innerScope;

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
      module('opal');
      inject(function($injector){
        BloodCultureLoader = $injector.get('BloodCultureLoader');
        $compile = $injector.get('$compile');
        $rootScope = $injector.get('$rootScope');
      });

      scope = $rootScope.$new();

      spyOn(BloodCultureLoader, "load").and.returnValue({
        then: function(fn){
          return fn({
            culture_order: angular.copy(culture_order),
            cultures: angular.copy(cultures)
          });
        }
      });

      scope.patient = {id: 12222}
      var tpl = '<div blood-culture-result-display><div id="greeting"></div></div>'
      var element = $compile(tpl)(scope);
      var input = angular.element($(element).find("#greeting")[0]);
      innerScope = input.scope();
      scope.$digest();
    });

    it("should make a call to load blood cultures on initialisation", function(){

      expect(BloodCultureLoader.load).toHaveBeenCalledWith(12222);
      expect(innerScope.culture_order).toEqual(culture_order);
      expect(innerScope.cultures).toEqual(cultures);

      // check that the scope is isolated
      expect(scope.culture_order).toBe(undefined);
      expect(scope.cultures).toBe(undefined);
    });

    it("should add a refresh option", function(){
      innerScope.refreshBloodCultures();
      expect(BloodCultureLoader.load.calls.count()).toBe(2);
    });
});
