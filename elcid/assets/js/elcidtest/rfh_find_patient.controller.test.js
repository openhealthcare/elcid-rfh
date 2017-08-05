describe('RfhFindPatientCtrl', function() {
  "use strict";
  var scope, parent, Episode, $controller, controller, $window;

  beforeEach(function(){
    module('opal.controllers');
    inject(function($injector){
      var $rootScope = $injector.get('$rootScope');
      $rootScope.fields = {
        demographics: {
          single: true,
          name: 'demographics',
          fields: [{
              name: "hospital_number",
              type: "string"
          }]
        },
        location: {
          single: true,
          name: 'location',
          fields: [{
              name: "ward",
              type: "string"
          }]
        }
      };
      parent = $rootScope.$new();
      parent.editing = {};
      scope = parent.$new();
      Episode = $injector.get('Episode');
      $controller = $injector.get('$controller');
    });

    $window = {alert: jasmine.createSpy()};

    scope.pathway = {
      save_url: "/some_url"
    };
    controller = $controller('RfhFindPatientCtrl', {
      scope: scope,
      Episode: Episode,
      step: {},
      episode: {},
      $window: $window
    });
  });

  it("should initialise the scope", function(){
    var fakeScope = {};
    controller.initialise(fakeScope);
    expect(fakeScope.demographics.hospital_number).toBe(undefined);
    expect(fakeScope.state).toBe('initial');
  });

  it("should change scope if we're unable to find a patient", function(){
    expect(scope.state).toBe('initial');
    scope.new_patient();
    expect(scope.state).toBe('editing_demographics');
  });

  it("should update the parent scope demographics", function(){
    expect(scope.state).toBe('initial');
    scope.demographics.hospital_number = "123"
    scope.new_patient();
    expect(parent.editing.demographics.hospital_number).toBe("123");
  });

  it("should look up hospital numbers", function(){
    spyOn(Episode, "findByHospitalNumber");
    scope.demographics.hospital_number = "12";
    scope.lookup_hospital_number();
    var allCallArgs = Episode.findByHospitalNumber.calls.all();
    expect(allCallArgs.length).toBe(1);
    var callArgs = allCallArgs[0].args;
    expect(callArgs[0]).toBe("12");
    expect(callArgs[1].newPatient).toEqual(scope.new_patient);
    expect(callArgs[1].newForPatient).toEqual(scope.new_for_patient);
  });

  it("should throw an error if the hospital number isn't found", function(){
    spyOn(Episode, "findByHospitalNumber");
    scope.demographics.hospital_number = "12";
    scope.lookup_hospital_number();
    var allCallArgs = Episode.findByHospitalNumber.calls.all();
    expect(allCallArgs.length).toBe(1);
    var callArgs = allCallArgs[0].args;
    expect(callArgs[1].error());
    expect($window.alert).toHaveBeenCalledWith('ERROR: More than one patient found with hospital number');
  });

  it('should only show next if state is has_demographics or editing_demographics', function(){
    scope.state = "has_demographics";
    expect(scope.showNext()).toBe(true);
    scope.state = "editing_demographics";
    expect(scope.showNext()).toBe(true);
  });

  it('should only show next if state is neither has_demographics or editing_demographics', function(){
    scope.state = "something";
    expect(scope.showNext()).toBe(false);
  });

  describe('new for patient', function(){
    beforeEach(function(){
      var fakePatient = {
        id: 1,
        demographics: [{
          hospital_number: "1",
          patient_id: 1
        }],
        episodes: [{
          location: [{
            ward: "1v"
          }],
          id: 3,
          demographics: [{
            hospital_number: "1",
            patient_id: 1
          }],
        }]
      };
      scope.new_for_patient(fakePatient);
    });

    it('should update the state', function(){
      expect(scope.state).toBe('has_demographics');
    })

    it("should update the demographics if a patient is found", function(){
      expect(parent.editing.demographics.hospital_number).toBe("1");
    });

    it('should update the save url', function(){
      expect(scope.pathway.save_url).toBe("/some_url/1/3");
    });

    it('should update the location', function(){
      expect(parent.editing.location.ward).toBe("1v");
    });

  })
});
