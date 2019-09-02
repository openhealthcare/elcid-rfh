describe('Elcid filters', function(){
  beforeEach(function(){
    module('opal');
  });
  describe('plural', function(){
    var plural;

    beforeEach(function(){
      inject(function($injector){
        plural  = $injector.get('pluralFilter');
      });
    });

    it('should be many', function(){
      expect(plural('box', 2, 'boxes')).toEqual('boxes');
    });

    it('should be singular', function(){
      expect(plural('box', 1, 'boxes')).toEqual('box');
    });

    it('should use the default', function(){
      expect(plural('ball', 3)).toEqual('balls');
    });
  });
});