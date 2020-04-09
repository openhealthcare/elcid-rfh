describe('ClinicalAdvice', function(){
  "use strict";
  var ClinicalAdvice, $httpBackend, item;
  beforeEach(function(){
    module('opal.services');
    inject(function($injector){
      ClinicalAdvice = $injector.get('ClinicalAdvice');
      $httpBackend = $injector.get('$httpBackend');
    });
  });

  describe('constructor', function(){
    it('should construct the editing object with item', function(){
      item = {
        id: 1,
        makeCopy(){
          return {
            id: 1,
            micro_input_icu_round_relation: {
              observation: {
                temperature: 38.5
              },
              icu_round: {
                ventilated: true
              }
            }
          }
        }
      }
      var clinicalAdvice = new ClinicalAdvice(item);
      expect(clinicalAdvice.isNew).toBe(false);
      expect(clinicalAdvice.editing.micro_input_icu_round_relation.observation.temperature).toBe(38.5);
      expect(clinicalAdvice.editing.micro_input_icu_round_relation.icu_round.ventilated).toBe(true);
    });

    it('should construct the editing object without item', function(){
      var clinicalAdvice = new ClinicalAdvice();
      expect(clinicalAdvice.isNew).toBe(true);
      expect(clinicalAdvice.editing.micro_input_icu_round_relation.icu_round).toEqual({});
      expect(_.isDate(clinicalAdvice.editing.when)).toBe(true);
    });
  });

  describe('elementName', function(){
    it('should return a string prefixed with the prefix', function(){
      var clnicalAdvice = new ClinicalAdvice();
      expect(clnicalAdvice.elementName('something').indexOf('something')).toBe(0);
    });
  });

  describe('save', function(){
    beforeEach(function(){

    });

    afterEach(function() {
      $httpBackend.verifyNoOutstandingExpectation();
      $httpBackend.verifyNoOutstandingRequest();
    });

  });
});