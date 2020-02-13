describe('RfhFindPatientCtrl', function() {
  "use strict";
  var scope, DemographicsSearch, $controller, controller, $window, ngProgressLite;

  beforeEach(function(){
    module('opal.controllers', function($provide){
      ngProgressLite = jasmine.createSpyObj([
        "set", "start", "done"
      ])
      $provide.service('ngProgressLite', function(){
        return ngProgressLite
      })
    });

    inject(function($injector){
      var $rootScope = $injector.get('$rootScope');
      scope = $rootScope.$new();
      DemographicsSearch = $injector.get('DemographicsSearch');
      $controller = $injector.get('$controller');
    });

    $window = {alert: jasmine.createSpy()};

    scope.pathway = {
      save_url: "/some_url"
    };
    controller = $controller('RfhFindPatientCtrl', {
      scope: scope,
      DemographicsSearch: DemographicsSearch,
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
    expect(fakeScope.hideFooter).toBe(true);
  });

  it("should change scope if we're unable to find a patient", function(){
    expect(scope.state).toBe('initial');
    scope.new_patient();
    expect(ngProgressLite.done).toHaveBeenCalled();
    expect(scope.state).toBe('editing_demographics');
    expect(scope.hideFooter).toBe(false);
  });

  it("should look up hospital numbers", function(){
    spyOn(DemographicsSearch, "find");
    scope.demographics.hospital_number = "12";
    scope.lookup_hospital_number();
    var allCallArgs = DemographicsSearch.find.calls.all();
    expect(allCallArgs.length).toBe(1);
    var callArgs = allCallArgs[0].args;
    expect(callArgs[0]).toBe("12");
    expect(callArgs[1].patient_not_found).toEqual(scope.new_patient);
    expect(callArgs[1].patient_found_in_elcid).toEqual(scope.new_for_patient);
    expect(callArgs[1].patient_found_upstream).toEqual(scope.new_for_patient);
    expect(ngProgressLite.set).toHaveBeenCalledWith(0);
    expect(ngProgressLite.start).toHaveBeenCalled();
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

  it('should update the next save_url if an patient is found', function(){
    scope.demographics = {patient_id: 1};
    scope.preSave({});
    expect(scope.pathway.save_url).toBe("/some_url/1");
  });

  it('should not update the next save_url if an patient is not found', function(){
    scope.preSave({});
    expect(scope.pathway.save_url).toBe("/some_url");
  });

  it("should update the demographics if a patient is found", function(){
    var fakePatient = {demographics: [{hospital_number: "1"}]};
    scope.new_for_patient(fakePatient);
    expect(scope.state).toBe('has_demographics');
    expect(scope.demographics).toBe(fakePatient.demographics[0]);
    expect(ngProgressLite.done).toHaveBeenCalled();
  });

  it("should hoist demographics to editing before saving", function(){
    scope.demographics = {hospital_number: "1"};
    var editing = {};
    scope.preSave(editing);
    expect(editing.demographics).toEqual(scope.demographics);
  });

  it("should update the tags if a patient is found", function(){
    var fakePatient = {
      demographics: [{hospital_number: "1"}],
      episodes: {
        1: {
          tagging: [{haem: true}]
        }
      }

    };
    scope.metadata = {tags: {haem: {}}};
    scope.new_for_patient(fakePatient);
    expect(scope.allTags).toEqual(['haem']);
  });

  it("should not update the tags if they're not in the metadata", function(){
    var fakePatient = {
      demographics: [{hospital_number: "1"}],
      episodes: {
        1: {
          tagging: [{haem: true}]
        }
      }

    };
    scope.metadata = {tags: {}};
    scope.new_for_patient(fakePatient);
    expect(scope.allTags).toEqual([]);
  });

  it("should update the from multiple episodes if found", function(){
    var fakePatient = {
      demographics: [{hospital_number: "1"}],
      episodes: {
        1: {
          tagging: [{
            haem: true,
            bacteraemia: true
          }],
        },
        3: {
          tagging: [{
            oncology: true
          }],
        }
      }

    };
    scope.metadata = {
      tags: {
        haem: {},
        bacteraemia: {},
        oncology: {}
      }
    };
    scope.new_for_patient(fakePatient);
    expect(scope.allTags).toEqual(['haem', 'bacteraemia', 'oncology']);
  });

  it("should update the tags removing duplicates if the patient is found", function(){
    var fakePatient = {
      demographics: [{hospital_number: "1"}],
      episodes: {
        1: {
          tagging: [{
            haem: true,
            bacteraemia: true
          }],
        },
        3: {
          tagging: [{
            bacteraemia: true
          }],
        }
      }

    };
    scope.metadata = {
      tags: {
        haem: {},
        bacteraemia: {},
        oncology: {}
      }
    };
    scope.new_for_patient(fakePatient);
    expect(scope.allTags).toEqual(['haem', 'bacteraemia']);
  });
});
