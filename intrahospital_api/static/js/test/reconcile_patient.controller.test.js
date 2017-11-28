describe('ReconcilePatientCtrl', function(){
  "use strict";
  var $rootScope, scope, $controller, shortDateFilter, controller;

  beforeEach(function(){
      module('opal');
      inject(function($injector){
        $rootScope = $injector.get('$rootScope');
        scope = $rootScope.$new();
        $controller = $injector.get('$controller');
        shortDateFilter = $injector.get('shortDateFilter');
        scope.editing.demographics = {
          first_name: "Wilma",
          surname: "Flintstone",
          date_of_birth: new Date(2010, 10, 1);
        }

        scope.editing.external_demographics = {
          first_name: "Betty",
          surname: "Rubble",
          date_of_birth: new Date(2009, 10, 1);
        }
        controller = $controller("ReconcilePatientCtrl", {
          scope: scope,
          shortDateFilter: shortDateFilter
        });
      });
  });

  it('should hoist demographics to scope', function(){
      expect(scope.demographics.first_name).toBe("Wilma");
      expect(scope.demographics.surname).toBe("Flintstone");
      expect(scope.demographics.date_of_birth).toBe("1/10/2010");
  });

  it('should replace demographics with external demographics', function(){
      expect(scope.editing.demographics.first_name).toBe("Betty");
      expect(scope.editing.demographics.surname).toBe("Rubble");
      expect(scope.editing.demographics.date_of_birth).toEqual(
        new Date(2009, 10, 1)
      );
  });

  it('should put external system on demographics', function(){
      expect(scope.editing.demographics.external_system).toBe("RFH Database");
  });
});
