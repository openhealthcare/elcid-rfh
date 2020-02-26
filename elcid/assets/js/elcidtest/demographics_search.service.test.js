describe("DemographicsSearch", function(){
  "use strict";

  var DemographicsSearch, $rootScope, $httpBackend, $window;

  beforeEach(function(){
    module('opal.services', function($provide){
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
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/?hospital_number=52').respond(
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

  it('should encode get params like hash', function(){
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/?hospital_number=%2352').respond(
      {status: "patient_found_in_elcid", patient: "some_patient"}
    );

    DemographicsSearch.find(
    "#52",
    {
      patient_found_in_elcid: function(some_result){
        called_result = some_result;
      }
    });

    $rootScope.$apply();
    $httpBackend.flush();
    expect(called_result).toBe("some_patient");
  });

  it('should encode get params like slash', function(){
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/?hospital_number=%2F52').respond(
      {status: "patient_found_in_elcid", patient: "some_patient"}
    );

    DemographicsSearch.find(
    "/52",
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
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/?hospital_number=52').respond(
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
  });

  it('should call patient found in hosptial', function(){
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/?hospital_number=52').respond(
      {status: "patient_found_upstream", patient: "some_patient"}
    );

    DemographicsSearch.find(
    "52",
    {
      patient_found_upstream: function(some_result){
        called_result = some_result;
      }
    });

    $rootScope.$apply();
    $httpBackend.flush();
    expect(called_result).toBe("some_patient");
  });

  it('should call patient not found', function(){
    var called_result = false;
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/?hospital_number=52').respond(
      {status: "patient_found_upstream"}
    );

    DemographicsSearch.find(
    "52",
    {
      patient_found_upstream: function(some_result){
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
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/?hospital_number=52').respond(
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
    $httpBackend.expectGET('/elcid/v0.1/demographics_search/?hospital_number=52').respond(
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
