describe('$exceptionHandler', function() {
  "use strict";

  var $exceptionHandler, $httpBackend, $rootScope, $log;
  var url = "/elcid/v0.1/error_emailer/";

  beforeEach(function(){
      module('opal.services');
      inject(function($injector){
          $exceptionHandler = $injector.get('$exceptionHandler');
          $httpBackend = $injector.get('$httpBackend');
          $rootScope = $injector.get('$rootScope');
          $log = $injector.get('$log');
      });
  });

  describe('test error post', function (){
    it('should post data to the end point and log', function () {
      spyOn($log, "error");
      $httpBackend.expectPOST(url).respond([]);
      $exceptionHandler("exception1", "cause1", {
        exception: "exception1", cause: "cause1"
      });
      $rootScope.$apply();
      $httpBackend.flush();
      expect($log.error).toHaveBeenCalledWith("exception1");
    });
  });
});
