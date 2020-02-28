describe('AddAntifungalPatients', function() {
  "use strict"
  var $scope, $controller, ctrl, DemographicsSearch;

  beforeEach(function(){
    module('opal.controllers');
    module('opal.services');

    inject(function($injector){
        var $rootScope   = $injector.get('$rootScope');
        $scope       = $rootScope.$new();
        $controller  = $injector.get('$controller');
        DemographicsSearch = $injector.get('DemographicsSearch');
    });

    spyOn(DemographicsSearch, "find");

    ctrl = $controller('AddAntifungalPatients', {
      $scope: $scope,
      DemographicsSearch: DemographicsSearch
    });
  });

  describe('flattenAndClean', function(){
    it('should split based on new lines/spaces/commas', function(){
      var hns = "1\n2,3 4";
      var expected = ["1", "2", "3", "4"];
      expect($scope.flattenAndClean(hns)).toEqual(expected);
    });

    it('shoud remove empty lines', function(){
      var hns = "1\n\n2";
      var expected = ["1", "2"];
      expect($scope.flattenAndClean(hns)).toEqual(expected);
    });

    it('should remove duplicates', function(){
      var hns = "1 1";
      var expected = ["1"];
      expect($scope.flattenAndClean(hns)).toEqual(expected);
    });

    it('should ignore the column header', function(){
      var hns = "patient_hospitalno 1";
      var expected = ["1"];
      expect($scope.flattenAndClean(hns)).toEqual(expected);
    });
  });

  describe('lookupAll', function(){
    it('should create patient forms from hospital numbers', function(){
      $scope.editing.hospitalNumbers = "1"
      $scope.lookupAll();
      expect($scope.patientForms.length).toBe(1);
      var pf = $scope.patientForms[0];
      expect(pf.state).toEqual($scope.states.SEARCHING);
      expect(pf.demographics.hospital_number).toBe("1");
      var callArgs = DemographicsSearch.find.calls.mostRecent().args;
      expect(callArgs[0]).toBe("1");
    });
  });

  describe('getSearchArgs', function(){
    var patientForm;
    var searchArgs;
    var result;
    beforeEach(function(){
      patientForm = {
        state: $scope.states.EDITING,
        error: false,
        demographics: {
          hospital_number: "1"
        }
      }
      searchArgs = $scope.getSearchArgs(patientForm);
      result = {demographics: [{"first_name": "Jane"}]};
    });

    it('should handle the case if the patient is found in elcid', function(){
      searchArgs[DemographicsSearch.PATIENT_FOUND_IN_ELCID](result);
      expect(patientForm.demographics).toEqual(result.demographics[0]);
      expect(patientForm.state).toEqual($scope.states.FOUND);
      expect(patientForm.error).toBe(false);
    });

    it('should handle the case if the patient is found upstream', function(){
      searchArgs[DemographicsSearch.PATIENT_FOUND_UPSTREAM](result);
      expect(patientForm.demographics).toEqual(result.demographics[0]);
      expect(patientForm.state).toEqual($scope.states.FOUND);
      expect(patientForm.error).toBe(false);
    });

    it('should handle the case if the patient is not found', function(){
      searchArgs[DemographicsSearch.PATIENT_NOT_FOUND]();
      expect(patientForm.demographics).toEqual({hospital_number: "1"});
      expect(patientForm.state).toEqual($scope.states.ERROR);
    });
  });

  describe('getDemographicsJson', function(){
    it('should return a stringifyed json of patient forms', function(){
      $scope.patientForms.push({
        state: $scope.states.FOUND,
        error: false,
        demographics: {
          hospital_number: "1"
        }
      });
      $scope.patientForms.push({
        state: $scope.states.FOUND,
        error: false,
        demographics: {
          hospital_number: "2"
        }
      });
      expect($scope.getDemographicsJson()).toEqual('[{"hospital_number":"1"},{"hospital_number":"2"}]');
    });
  });

  describe('lookup', function(){
    var patientForm;
    beforeEach(function(){
      patientForm = {
        state: $scope.states.EDITING,
        error: false,
        demographics: {
          hospital_number: "1"
        }
      }
    });

    it('should do nothing if hospital number is not populated', function(){
      patientForm.demographics.hospital_number = undefined;
      $scope.lookup(patientForm);
      expect(DemographicsSearch.find).not.toHaveBeenCalled();
    });

    it('should do nothing if hospital number is an empty string', function(){
      patientForm.demographics.hospital_number = "";
      $scope.lookup(patientForm);
      expect(DemographicsSearch.find).not.toHaveBeenCalled();
    });

    it('should query the demographics search', function(){
      patientForm.demographics.hospital_number = "1";
      spyOn($scope, "getSearchArgs").and.returnValue("some search args");
      $scope.lookup(patientForm);
      expect(DemographicsSearch.find).toHaveBeenCalledWith(
        "1", "some search args"
      )
    });
  });

  describe('filterForms', function(){
    it('should query patient forms', function(){
      $scope.patientForms = []
      var shouldBeReturned = {
        state: $scope.states.EDITING,
        error: false,
        demographics: {
          hospital_number: "1"
        }
      };
      $scope.patientForms.push(shouldBeReturned);
      $scope.patientForms.push({
        state: $scope.states.FOUND,
        error: false,
        demographics: {
          hospital_number: "2"
        }
      });
      expect($scope.filterForms({state: $scope.states.EDITING})).toEqual([shouldBeReturned]);
    })
  });

  describe('remove', function(){
    it('should remove an element from an error', function(){
      $scope.patientForms = []
      var shouldBeRetained = {
        state: $scope.states.EDITING,
        error: false,
        demographics: {
          hospital_number: "1"
        }
      };
      $scope.patientForms.push(shouldBeRetained);
      $scope.patientForms.push({
        state: $scope.states.FOUND,
        error: false,
        demographics: {
          hospital_number: "2"
        }
      });
      $scope.remove(1);
      expect($scope.patientForms).toEqual([shouldBeRetained]);
    });

    it('should change the state if nothing is left', function(){
      $scope.state = $scope.states.ADD_PATIENTS;
      $scope.patientForms = [];
      $scope.patientForms.push({
        state: $scope.states.FOUND,
        error: false,
        demographics: {
          hospital_number: "2"
        }
      });

      $scope.remove(0);
      expect($scope.state).toEqual($scope.states.LOOKUP_PATIENTS);
    });
  });

  describe('can save', function(){
    var patientForm;

    beforeEach(function(){
      patientForm = {
        state: $scope.states.FOUND,
        error: false,
        demographics: {
          hospital_number: "1"
        }
      }

      $scope.patientForms.push(patientForm);
    });


    it('should be false if some forms are not found', function(){
      patientForm.state = $scope.states.SEARCHING;
      expect($scope.canSave()).toBeFalse();
    });

    it('should be false even if one of the forms is found', function(){
      var otherPatientForm = {
        state: $scope.states.SEARCHING,
        error: false,
        demographics: {
          hospital_number: "1"
        }
      };

      $scope.patientForms.push(otherPatientForm);
      expect($scope.canSave()).toBeFalse();
    });

    it('should be true, if all the forms are found', function(){
      expect($scope.canSave()).toBeTrue();
    });
  });

  describe('init', function(){
    it('should initialise the model to editing to empty and state to lookup', function(){
      expect($scope.state).toEqual($scope.states.LOOKUP_PATIENTS);
      expect($scope.editing.hospitalNumbers).toEqual("");
    });
  });
});