describe('TestSummaryLoader', function() {
  "use strict";
  var KeyInvestigationsLoader, $window, $httpBackend, getRequest;

  beforeEach(function(){
    module('opal.services');
    inject(function($injector) {
      KeyInvestigationsLoader = $injector.get('KeyInvestigationsLoader');
      $window = $injector.get('$window');
      $httpBackend = $injector.get('$httpBackend');
    });

    spyOn($window, 'alert');
    getRequest = $httpBackend.expectGET('/something/11/')
  });

  it('should query by the with the patient url and return a promise', function(){
    getRequest.respond({});
    var result = KeyInvestigationsLoader.load('/something/', 11)
    $httpBackend.flush();
    $httpBackend.verifyNoOutstandingRequest();
    $httpBackend.verifyNoOutstandingExpectation();
    expect(!!result.then).toBe(true);
  });

  it('should raise an error if the tests fails to load', function(){
    getRequest.respond(
      409, {'error': 'Fail'}
    );
    KeyInvestigationsLoader.load('/something/', 11);
    $httpBackend.flush();
    $httpBackend.verifyNoOutstandingRequest();
    $httpBackend.verifyNoOutstandingExpectation();
    expect($window.alert).toHaveBeenCalledWith('Test summary could not be loaded');
  });
});
