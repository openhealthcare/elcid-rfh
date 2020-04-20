describe('TbSymptomComplexCrtl', function(){
  "use strict";
  var controller, scope, $rootScope, $controller;

  beforeEach(function(){
      module('opal.controllers');
      inject(function($injector){
          $rootScope   = $injector.get('$rootScope');
          $controller  = $injector.get('$controller');
      });

      scope = $rootScope.$new();
      scope.editing = {demographics: {}, social_history: {}};

      controller = $controller('TbSymptomComplexCrtl', {
          $controller: $controller,
          step: {},
          scope: scope,
          episode: {
              newItem: function(){
                    return {
                      makeCopy: function(){}
                  }
              }
          }
      });
  })

  describe('set up', function(){

    function setUpScope(editing){
        scope = $rootScope.$new();
        scope.editing = angular.copy(editing);

        $controller('TbSymptomComplexCrtl', {
            $controller: $controller,
            step: {},
            scope: scope,
            episode: {
                newItem: function(){
                      return {
                        makeCopy: function(){}
                    }
                }
            }
        });

        return scope
    }

    it("should set up symptom_complex if symptom_complex is a populated array", function(){
        var editing = {
            symptom_complex: [
                {symptoms: ["Cough (Dry)"]}
            ]
        }
        var stepScope = setUpScope(editing);
        expect(stepScope.editing.symptom_complex).toEqual(editing.symptom_complex[0]);
    });

    it("should set up symptom_complex if symptom_complex is an empty array", function(){
        var editing = {
            symptom_complex: []
        }
        var stepScope = setUpScope(editing);
        expect(stepScope.editing.symptom_complex).toEqual({symptoms: []});
    });

    it("should set up symptoms symptom_complex if symptoms is missing", function(){
        var editing = {
            symptom_complex: {}
        }
        var stepScope = setUpScope(editing);
        expect(stepScope.editing.symptom_complex).toEqual({symptoms: []});
    });

    it("should set up lymph_node_swelling_site if lymph_node_swelling_site is a populated array", function(){
        var editing = {
            lymph_node_swelling_site: [
                {site: "neck"}
            ]
        }
        var stepScope = setUpScope(editing);
        expect(stepScope.editing.lymph_node_swelling_site).toEqual({site: "neck"});
    });

    it("should set up lymph_node_swelling_site if lymph_node_swelling_site is an empty array", function(){
        var editing = {
            lymph_node_swelling_site: []
        }
        var stepScope = setUpScope(editing);
        expect(stepScope.editing.lymph_node_swelling_site).toEqual({});
    });
  });

  describe('test change', function(){
    beforeEach(function(){
      _.each(scope.tbSymptomFields, function(v, k){
        scope.tbSymptom[k] = false;
      });
    });

    it('should update the radio buttons according to the symptoms model changes', function(){
        var symptomField = 'Fever'
        scope.tbSymptom[symptomField] = true;
        scope.updateSymptoms(symptomField);
        expect(_.contains(scope.editing.symptom_complex.symptoms, "Fever")).toBe(true);
    });

    it('should update the model based on radio button changes', function(){
        var symptomField = "Fever";
        scope.editing.symptom_complex.symptoms.push(symptomField);
        scope.updateTbSymptoms()
        expect(scope.tbSymptom["Fever"]).toBe(true);
    });

  });
});
