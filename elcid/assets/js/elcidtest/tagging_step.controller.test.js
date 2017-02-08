describe('TaggingStepCtrl', function() {
    "use strict";
    var $controller;

    beforeEach(function(){
        module('opal.controllers');
        inject(function($injector){
            $controller  = $injector.get('$controller');
        });
    });

    it('should add a tagging dictionary onto the controller', function(){
      var scope = {editing: {}};
      $controller('TaggingStepCtrl', {
        scope: scope, step: {}, episode: {}
      });

      expect(scope.editing.tagging).toEqual({});
    });
});
