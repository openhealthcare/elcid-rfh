angular.module('opal.services').service('BloodCultureHelper', function(){
  "use strict";

  /*
   Blood cultures are dealt with in a staged manner
   first you perform 4 fish tests

   1. Quick Fish -> Yeast, possible results
      - Candida albicans (C. albicans)
      - Candida parapsilosis (C.parapsilosis)
      - Candida glabrata (C. glabrata)
      - Negative

    2. GPC Staph -> Gram positive cocci in clusters, possible results
      - Staphylococcus aureus (S.aureus)
      - Coagulase-negative staphylococci (CNS)
      - Negative

    3. GPC Strep -> Gram positive cocci in chains, possible results
      - Enterococcus faecalis  (E. faecalis)
      - Other enterococci
      - Negative

    3. GGram -ve Rods -> GNR
      - E.coli
      - K. pneumoniae
      - P. aeruginosa
      - Negative
  */

  var GRAM_STAIN_TO_FISH_TEST = {
    Yeast: "QuickFISH",
    "Gram +ve Cocci Cluster": "GPC Staph",
    "Gram +ve Cocci Chains": "GPC Strep",
    "Gram -ve Rods": "GNR"
  };
  var FISH_TO_GRAM_STAIN_RESULT = _.invert(GRAM_STAIN_TO_FISH_TEST);
  var BLOOD_CULTURE_TESTS = _.keys(FISH_TO_GRAM_STAIN_RESULT);
  BLOOD_CULTURE_TESTS.push("Gram Stain");
  BLOOD_CULTURE_TESTS.push("Organism");

  var Isolate = function(aerobic, isolate_number, lab_tests){
    var self = this;
    this.aerobic = aerobic;
    if(isolate_number){
      this.isolate_number = isolate_number;
    }
    else{
      this.isolate_number = 1;
    }
    this.lab_tests = lab_tests || [];

    // this is used as the model for the mult select gram stains
    this.gramStainTests = {};

    self.initialise = function(){
      var gramStains = _.filter(self.lab_tests, function(lab_test){
        return lab_test.lab_test_type === "Gram Stain";
      });

      var gramStainResults = _.pluck(_.pluck(gramStains, "result"), "result");
      // included to to enforce order
      self.gramStainResultChoices = [
        "Yeast",
        "Gram +ve Cocci Cluster",
        "Gram +ve Cocci Chains",
        "Gram -ve Rods"
      ];

      _.each(self.gramStainResultChoices, function(gramStainResultChoice){
        self.gramStainTests[gramStainResultChoice] = _.contains(gramStainResults, gramStainResultChoice);
      });

      var organismTestExists = !!_.find(self.lab_tests, {
        lab_test_type: "Organism"
      })

      if(!organismTestExists){
        self.lab_tests.push({
          _client: {
            id: _.uniqueId('lab_test'),
            resistantName: _.uniqueId('lab_test_resistant'),
            sensitiveName: _.uniqueId('lab_test_sensitive'),
          },
          lab_test_type: "Organism",
          extras: {
            aerobic: self.aerobic,
            isolate: self.isolate_number
          }
        });
      }
    };

    self.initialise();

    this.isFishTest = function(lab_test){
      return _.contains(GRAM_STAIN_TO_FISH_TEST, lab_test.lab_test_type);
    };

    this.updateTests = function(){
      _.each(self.gramStainTests, function(shouldExist, testResult){
        var fishTestName = GRAM_STAIN_TO_FISH_TEST[testResult];
        var fishTest = _.find(self.lab_tests, function(lab_test){
          return lab_test.lab_test_type === fishTestName;
        });
        var gramStain = _.find(self.lab_tests, function(lab_test){
          return lab_test.lab_test_type === "Gram Stain" && lab_test.result.result === testResult;
        });
        if(shouldExist){
          if(!fishTest){
            self.lab_tests.push({
              _client: {
                id: _.uniqueId('lab_test')
              },
              lab_test_type: fishTestName,
              extras: {
                aerobic: self.aerobic,
                isolate: self.isolate_number
              }
            });
          }
          if(!gramStain){
            self.lab_tests.push({
              _client:{
                id: _.uniqueId('lab_test')
              },
              lab_test_type: "Gram Stain",
              result: {result: testResult},
              extras: {
                aerobic: self.aerobic,
                isolate: self.isolate_number
              }
            });
          }
        }
        else{
          self.lab_tests = _.filter(self.lab_tests, function(lab_test){
            if(lab_test === fishTest && !fishTest.id){
              return false;
            }
            if(lab_test === gramStain){
              return false;
            }
            return true
          });
        }
      });
    };
  };

  var BloodCulture = function(source, date_ordered, lab_number, lab_tests){
    var self = this;
    this.source = source;
    this.date_ordered = date_ordered;
    this.lab_number = lab_number;
    this.isolates = groupLabTestsToIsolates(lab_tests || []);
    this.nextIsolateNumber = null;

    if(this.isolates.length){
      // we're just looking for a unique number for this isolate for all added isolates
      var highestIsolateNumber = _.max(self.isolates, function(isolate){
        return isolate.lab_tests[0].extras.isolate;
      }).lab_tests[0].extras.isolate;

      this.nextIsolateNumber = Math.max(highestIsolateNumber, this.isolates.length) + 1;
    }

    this.getIsolates = function(aerobic){
      return _.filter(self.isolates, function(isolate){
        return aerobic === !!isolate.aerobic;
      });
    };

    this.addIsolate = function(aerobic){
      self.isolates.push(new Isolate(aerobic, self.nextIsolateNumber, []));
      self.nextIsolateNumber += 1;
    };

    this.getLabTests = function(){
      var labTests = [];
      _.each(self.isolates, function(isolate){
        _.each(isolate.lab_tests, function(labTest){
          labTest.extras.source = self.source;
          labTest.extras.lab_number = self.lab_number;
          labTest.date_ordered = self.date_ordered;
          labTests.push(labTest);
        });
      });

      return labTests;
    };

    this.removeIsolate = function(isolate){
      var idx = _.findIndex(self.isolates, function(existing_isolate){
        return existing_isolate.isolate_number === isolate.isolate_number;
      });
      self.isolates.splice(idx, 1);
    };
  };

  var groupLabTestsToCultures = function(lab_tests){
    /*
    * Groups lab tests by lab_test, date ordered, lab_number
    * then casts them to blood cultures
    */
    var grouped = _.groupBy(lab_tests, function(lab_test){
      var dt;

      return [
        lab_test.extras.source,
        lab_test.date_ordered,
        lab_test.extras.lab_number
      ];
    });

    return _.map(grouped, function(group){
      return new BloodCulture(
        group[0].extras.source,
        group[0].date_ordered,
        group[0].extras.lab_number,
        group
      );
    });
  };

  var groupLabTestsToIsolates = function(lab_tests){
    /*
    * Groups lab tests by isolate and anaerobic/aerobic
    * (assumes groupLabTestsToCultures has already been called)
    */
    var grouped = _.groupBy(lab_tests, function(lab_test){
      return [lab_test.extras.aerobic, lab_test.extras.isolate];
    });

    return _.map(grouped, function(group){
      return new Isolate(
        group[0].extras.aerobic,
        group[0].extras.isolate,
        group
      );
    });
  };

  var BloodCultureHelper = function(labTests){
    if(!_.isArray(labTests)){
      labTests = [labTests];
    }
    var self = this;
    var pertinantLabTests = _.filter(labTests, function(labTest){
      return _.contains(BLOOD_CULTURE_TESTS, labTest.lab_test_type);
    });

    this.bloodCultures = groupLabTestsToCultures(pertinantLabTests);

    this.getAllLabTests = function(){
      var labTests = [];
       _.each(self.bloodCultures, function(bloodCulture){
        labTests = labTests.concat(bloodCulture.getLabTests())
      });
      return labTests;
    }

    if(!this.bloodCultures.length){
      this.bloodCultures.push(new BloodCulture());
    }

    this.preSave = function(editing){
      var labTests = [];
      if(!_.isArray(editing.lab_test)){
        editing.lab_test = [editing.lab_test];
      }
      editing.lab_test = _.filter(editing.lab_test, function(lab_test){
        return !_.contains(BLOOD_CULTURE_TESTS, lab_test.lab_test_type);
      });
      editing.lab_test = editing.lab_test.concat(self.getAllLabTests());
    }

    this.addBloodCulture = function(){
      this.bloodCultures.push(new BloodCulture());
    };

    this.removeBloodCulture = function(idx){
      self.bloodCultures.splice(idx, 1);
      if(!self.bloodCultures.length){
        self.bloodCultures.push(new BloodCulture());
      }
    }
  };

  return BloodCultureHelper;
});
