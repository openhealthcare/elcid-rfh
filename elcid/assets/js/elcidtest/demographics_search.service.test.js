describe("DemographicsSearch", function(){
  "use strict";

  var DemographicsSearch, $rootScope, $httpBackend, $window, ngProgressLite;

  beforeEach(function(){
    module('opal.services', function($provide){
      ngProgressLite = jasmine.createSpyObj([
        "set", "start", "done"
      ])
      $provide.service('ngProgressLite', function(){
        return ngProgressLite
      });

    });
    inject(function($injector){
      DemographicsSearch  = $injector.get('DemographicsSearch');
      $rootScope = $injector.get('$rootScope');
      $httpBackend = $injector.get('$httpBackend');
      $window = $injector.get('$window');
    });
  });

  afterEach(function() {
      $httpBackend.verifyNoOutstandingExpectation();
      $httpBackend.verifyNoOutstandingRequest();
  });

  it('should blow up if we pass in an unknown call back', function(){
    expect(function(){
      DemographicsSearch.find(
      "1231231221",
      {
        blahblah: function(){}
      });
    }).toThrow("unknown call back");

  });

  it('should call find patient found in elcid', function(){
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/52/').respond(
      {status: "patient_found_in_elcid", patient: "some_patient"}
    );

    DemographicsSearch.find(
    "52",
    {
      patient_found_in_elcid: function(some_result){
        called_result = some_result;
      }
    });

    $rootScope.$apply();
    $httpBackend.flush();
    expect(called_result).toBe("some_patient");
  });

  it('should call done on the ng progress lite', function(){
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/52/').respond(
      {status: "patient_found_in_elcid", patient: "some_patient"}
    );

    DemographicsSearch.find(
    "52",
    {
      patient_found_in_elcid: function(some_result){
        called_result = some_result;
      }
    });

    $rootScope.$apply();
    $httpBackend.flush();
    expect(ngProgressLite.set).toHaveBeenCalledWith(0);
    expect(ngProgressLite.start).toHaveBeenCalled();
    expect(ngProgressLite.done).toHaveBeenCalled();
  });

  it('should call patient found in hosptial', function(){
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/52/').respond(
      {status: "patient_found_in_hospital", patient: "some_patient"}
    );

    DemographicsSearch.find(
    "52",
    {
      patient_found_in_hospital: function(some_result){
        called_result = some_result;
      }
    });

    $rootScope.$apply();
    $httpBackend.flush();
    expect(called_result).toBe("some_patient");
  });

  it('should call patient not found', function(){
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/52/').respond(
      {status: "patient_found_in_hospital"}
    );

    DemographicsSearch.find(
    "52",
    {
      patient_found_in_hospital: function(some_result){
        called_result = undefined;
      }
    });

    $rootScope.$apply();
    $httpBackend.flush();
    expect(_.isUndefined(called_result)).toBe(true);
  });

  it('should raise an alert if an unknown status is returned', function(){
    spyOn($window, "alert");
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/52/').respond(
      {status: "blah blah"}
    );

    DemographicsSearch.find("52");

    $rootScope.$apply();
    $httpBackend.flush();
    expect($window.alert).toHaveBeenCalledWith(
      "DemographicsSearch could not be loaded"
    )
  });

  it('should blow up if the search errors', function(){
    spyOn($window, "alert");
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/52/').respond(
      500, "NO"
    );

    DemographicsSearch.find("52");

    $rootScope.$apply();
    $httpBackend.flush();
    expect($window.alert).toHaveBeenCalledWith(
      "DemographicsSearch could not be loaded"
    )
  });
});
