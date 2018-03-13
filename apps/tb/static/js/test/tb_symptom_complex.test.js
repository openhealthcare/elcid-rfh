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
        console.error(scope.editing.symptom_complex.symptoms);
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
