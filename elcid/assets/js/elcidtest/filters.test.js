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

  describe('startsWith', function(){
    var startsWith;

    beforeEach(function(){
      inject(function($injector){
        startsWith  = $injector.get('startsWithFilter');
      });
    });

    it('should return false if the initial string is not populated', function(){
      expect(startsWith(null, "hello")).toBe(false);
    });

    it('should handle case sensitivity true', function(){
      expect(startsWith("hello", "he")).toBe(true);
    });

    it('should handle case sensitivity false', function(){
      expect(startsWith("hello", "He", true)).toBe(false);
    });

    it('should handle case insensitivity true', function(){
      expect(startsWith("hello", "He")).toBe(true);
    });

    it('should handle case insensitivity false', function(){
      expect(startsWith("hello", "oter")).toBe(false);
    });
  });
});