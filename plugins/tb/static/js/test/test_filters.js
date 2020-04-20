describe('filters', function() {
  "use strict";
  var bmiFilter;

  beforeEach(module('opal.filters'));

  beforeEach(function(){
      inject(function($injector){
          bmiFilter  = $injector.get('bmiFilter');
      });
  });


  describe('bmi', function(){
    it("should return undefined if height/weight aren't populated", function(){
      expect(bmiFilter(undefined, 1)).toBe(undefined);
      expect(bmiFilter(undefined, undefined)).toBe(undefined);
      expect(bmiFilter(undefined, 1)).toBe(undefined);
    })
  });

});
