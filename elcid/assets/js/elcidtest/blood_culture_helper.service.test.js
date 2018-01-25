describe("BloodCultureHelper", function(){
  "use strict";
  var BloodCultureHelper, bloodCultureHelper;

  var getBloodCulture = function(overrides){
    var bc = {'consistency_token': '689a9b05',
           'created': '11/01/2017 12:25:59',
           'created_by_id': 1,
           'datetime_ordered': '04/01/2017',
           'datetime_received': undefined,
           'external_identifier': undefined,
           'external_system': undefined,
           'extras': {
            'aerobic': true,
            'isolate': 2,
            'lab_number': '123122',
            'source': 'Hickman'},
           'id': 35,
           'lab_test_type': 'Organism',
           'patient_id': 15,
           'resistant_antibiotics': [],
           'result': {'consistency_token': 'cc12d7b9',
            'created': '11/01/2017 12:25:59',
            'created_by_id': 1,
            'extras': {},
            'id': 29,
            'lab_test_id': 35,
            'name': 'result',
            'observation_type': 'Organism',
            'result': 'Acinetobacter',
            'updated': '11/01/2017 12:28:42',
            'updated_by_id': 1},
           'sensitive_antibiotics': [],
           'status': undefined,
           'updated': '11/01/2017 12:28:42',
           'updated_by_id': 1};

      _.extend(bc, overrides);
      return bc;
  }

  var labTests = [
      // blood culture 1, isolate 1
      getBloodCulture({
        datetime_ordered: '04/01/2017',
        lab_test_type: 'Organism',
        result: {result: 'Acinetobacter'},
        extras: {
         aerobic: true,
         isolate: 2,
         lab_number: '123122',
         source: 'Hickman'}
      }),
      getBloodCulture({
        datetime_ordered: '04/01/2017',
        lab_test_type: 'Gram Stain',
        result: {result: 'Yeast'},
        extras: {
         aerobic: true,
         isolate: 2,
         lab_number: '123122',
         source: 'Hickman'}
      }),
      // blood culture 1, isolate 2
      getBloodCulture({
        datetime_ordered: '04/01/2017',
        lab_test_type: 'QuickFISH',
        result: {result: 'C. glabrata'},
        extras: {
         aerobic: false,
         isolate: 3,
         lab_number: '123122',
         source: 'Hickman'}
      }),
      // blood culture 2, isolate 1
      getBloodCulture({
        datetime_ordered: '05/01/2017',
        lab_test_type: 'QuickFISH',
        result: {result: 'C. glabrata'},
        extras: {
         aerobic: false,
         isolate: 4,
         lab_number: '123123',
         source: 'other'}
      })
    ];

  beforeEach(function(){
    module('opal.services');
    inject(function($injector){
      BloodCultureHelper  = $injector.get('BloodCultureHelper');
      bloodCultureHelper = new BloodCultureHelper(angular.copy(labTests));
    });
  });

  describe("BloodCultureHelper", function(){
    it('should group isolates appropriately', function(){
      expect(bloodCultureHelper.bloodCultures.length).toBe(2);
      expect(bloodCultureHelper.bloodCultures[0].source).toBe('Hickman');
      expect(bloodCultureHelper.bloodCultures[0].lab_number).toBe('123122');
      expect(bloodCultureHelper.bloodCultures[0].datetime_ordered).toBe('04/01/2017');

      expect(bloodCultureHelper.bloodCultures[1].source).toBe('other');
      expect(bloodCultureHelper.bloodCultures[1].lab_number).toBe('123123');
      expect(bloodCultureHelper.bloodCultures[1].datetime_ordered).toBe('05/01/2017');
    });

    it('should return all lab tests', function(){
      // it adds in an additional empty organism test for the two isolates
      // without an organism
      expect(bloodCultureHelper.getAllLabTests().length).toBe(6);
    });

    it('should add blood cultures', function(){
      bloodCultureHelper.addBloodCulture();
      expect(bloodCultureHelper.bloodCultures.length).toBe(3);
    });

    it('should remove blood cultures', function(){
      bloodCultureHelper.removeBloodCulture(0);
      expect(bloodCultureHelper.bloodCultures.length).toBe(1);
      expect(bloodCultureHelper.getAllLabTests().length > labTests.length).not.toBe(true);
    });
  });

  describe("BloodCulture", function(){
    it('should return isolates filtered by aerobic', function(){
      var result = bloodCultureHelper.bloodCultures[0].getIsolates(true)[0];
      expect(result.lab_tests[0].extras.aerobic).toBe(true);
    });

    it('should return isolates filtered by anaerobic', function(){
      var result = bloodCultureHelper.bloodCultures[0].getIsolates(false)[0];
      expect(result.lab_tests[0].extras.aerobic).toBe(false);
    });

    it('should return labtests with the addition of its extras and datetime_ordered', function(){
      bloodCultureHelper.bloodCultures[0].datetime_ordered = '05/01/2017'
      var labTests = bloodCultureHelper.bloodCultures[0].getLabTests();
      expect(labTests.length > 0).toBe(true);
      _.each(labTests, function(labTest){
        expect(labTest.datetime_ordered).toBe('05/01/2017');
      });
    });

    it('should add aerobic isolates', function(){
      bloodCultureHelper.bloodCultures[0].addIsolate(true);
      var newIsolate = _.last(bloodCultureHelper.bloodCultures[0].isolates);
      expect(newIsolate.aerobic).toBe(true);
      expect(newIsolate.isolate_number).toBe(4);
    });

    it('should set the isolate number to 1 if currently all isolates are number null', function(){
      var lts = angular.copy([labTests[0]]);
      _.each(lts, function(lt){
        lt.extras.isolate = null;
      });
      bloodCultureHelper = new BloodCultureHelper(angular.copy(lts));
      bloodCultureHelper.bloodCultures[0].addIsolate(true);
      var allLabTests = bloodCultureHelper.getAllLabTests()
      expect(allLabTests[1].extras.isolate).toBe(2);
    });

    it('should add anaerobic isolates', function(){
      bloodCultureHelper.bloodCultures[0].addIsolate(false);
      var newIsolate = _.last(bloodCultureHelper.bloodCultures[0].isolates);
      expect(newIsolate.aerobic).toBe(false);
    });

    it('should remove isolates', function(){
      var firstIsolate = bloodCultureHelper.bloodCultures[0].isolates[0]
      bloodCultureHelper.bloodCultures[0].removeIsolate(firstIsolate);
      expect(bloodCultureHelper.bloodCultures[0].isolates.length).toBe(1)
      expect(bloodCultureHelper.bloodCultures[0].isolates[0]).not.toEqual(firstIsolate);
    });
  });

  describe("Isolate", function(){
    var isolate;

    beforeEach(function(){
      isolate = bloodCultureHelper.bloodCultures[0].isolates[0];
    });

    var getGramStains = function(isolate){
      return _.filter(isolate.lab_tests, function(lab_test){
        return lab_test.lab_test_type === 'Gram Stain';
      });
    }

    it('should initialise the gram stain choices', function(){
      var gramStains = getGramStains(isolate);
      expect(gramStains.length).toEqual(1);
      expect(gramStains[0].result.result).toEqual("Yeast");
      expect(isolate.gramStainTests.Yeast).toBe(true);
      expect(isolate.gramStainTests["Gram +ve Cocci Cluster"]).toBe(false);
      expect(isolate.gramStainTests["Gram +ve Cocci Chains"]).toBe(false);
      expect(isolate.gramStainTests["Gram -ve Rods"]).toBe(false);
    })

    it("should create gram stain choices, depending on existin gram stain results", function(){
      expect(_.filter(isolate.lab_tests, {lab_test_type: "GNR"}).length).toBe(0);
      isolate.gramStainTests["Gram -ve Rods"] = true;
      isolate.updateTests();
      var gramStains = getGramStains(isolate);
      expect(_.last(gramStains).result.result).toEqual("Gram -ve Rods");
      expect(_.filter(isolate.lab_tests, {lab_test_type: "GNR"}).length).toBe(1);
    });

    it('should remove gram stains when results indicate it should', function(){
      isolate.updateTests();
      expect(isolate.gramStainTests.Yeast).toBe(true);
      isolate.gramStainTests.Yeast = false;
      isolate.updateTests();
      expect(_.filter(isolate.lab_tests, {lab_test_type: "QuickFISH"}).length).toBe(0);
      expect(_.filter(isolate.lab_tests, {lab_test_type: "Gram Stain"}).length).toBe(0);
    });

    it("should create an organism test if one doesn't exist", function(){
      var isolate = bloodCultureHelper.bloodCultures[1].isolates[0];
      var organism = _.find(isolate.lab_tests, {lab_test_type: "Organism"});
      expect(organism.result).toBe(undefined);
    });

    it("should not create an organism test if one does exist", function(){
      var organismTests =_.filter(isolate.lab_tests, {lab_test_type: "Organism"});
      expect(organismTests.length).toBe(1);
      expect(organismTests[0].result.result).toEqual("Acinetobacter");
    });

    it("should identify lab tests that are of the fish test type", function(){
      expect(isolate.isFishTest({lab_test_type: "not a fish test"})).toBe(false);
      expect(isolate.isFishTest({lab_test_type: "QuickFISH"})).toBe(true);
      expect(isolate.isFishTest({lab_test_type: "GPC Staph"})).toBe(true);
      expect(isolate.isFishTest({lab_test_type: "GPC Strep"})).toBe(true);
      expect(isolate.isFishTest({lab_test_type: "GNR"})).toBe(true);
    });


  });
});
