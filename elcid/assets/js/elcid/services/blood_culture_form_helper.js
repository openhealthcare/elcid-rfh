angular.module('opal.services').factory('BloodCultureFormHelper', function(){
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

    3. GNR -> Gram Stain
      - E.coli
      - K. pneumoniae
      - P. aeruginosa
      - Negative
  */

  var BloodCultureFormHelper = function(bloodCulture, metadata){
      var self = this;
      self.gramStainMeta = _.find(metadata.lab_test, function(lt){
        return lt.name === 'gram_stain';
      }).result_choices;

      var LabTest = function(test_name, result){
        this.date_ordered = moment().format("DD/MM/YYYY");
        this.date_received = moment().format("DD/MM/YYYY");
        this.test_name = test_name;
        this.result = result;
      };

      self.fishTests = {
          "Yeast": "QuickFISH",
          "Gram +ve Cocci Cluster": "GPC Staph",
          "Gram +ve Cocci Chains": "GPC Strep",
          "Gram -ve Rods": "GNR"
      };

      self.addAerobic = function(){
        // insert an element between the last aerobic and the
        // first anaerobic
        var firstAnaerobicIndex = _.findIndex(bloodCulture.isolates, function(bc){
          return !bc.aerobic;
        });
        var isolate = {
          aerobic: true,
          lab_tests: [new LabTest("Organism")],
        };

        if(firstAnaerobicIndex=== -1){
          bloodCulture.isolates.push(isolate);
        }
        else{
          bloodCulture.isolates.splice(firstAnaerobicIndex, 0, isolate);
        }
      };

      self.addAnaerobic = function(){
        bloodCulture.isolates.push({
            aerobic: false,
            lab_tests: [new LabTest("Organism")],
        });
      };

      self.aerobicIsolates = function(){
        return _.filter(bloodCulture.isolates, function(bc){
            return bc.aerobic;
        });
      };

      self.anaerobicIsolates = function(){
        return _.filter(bloodCulture.isolates, function(bc){
            return !bc.aerobic;
        });
      };

      self.delete = function(index, isolate){
        if(isolate.aerobic){
            bloodCulture.isolates.splice(index, 1);
        }
        else{
            var position = self.aerobicIsolates().length + index;
            bloodCulture.isolates.splice(position, 1);
        }
      };

      /*
      * when we update tests, we nuke all existing tests, unless they have an id
      * if they have an id, the user can nuke them just by setting them to 'not done'
      * and saving them, in which case they will be deleted by the server
      */
      self.updateTests = function(){
        bloodCulture.lab_tests = _.filter(bloodCulture.lab_tests, function(lt){
          return lt.id || (!_.contains(_.values(self.fishTests), lt.test_name) && lt.test_name !== "Gram Stain");
        });

        _.each(self.multiGramStain, function(v, k){
          var gramStainExists = _.find(bloodCulture.lab_tests, function(lt){
            return lt.test_name === "Gram Stain" && lt.result === k;
          });

          if(v){
            if(self.fishTests[k]){
              var testExists = _.find(bloodCulture.lab_tests, function(lt){
                return lt.test_name === self.fishTests[k];
              });

              if(!testExists){
                var fishTest = new LabTest(self.fishTests[k], "Not Done");
                bloodCulture.lab_tests.push(fishTest);
              }
            }

            if(!gramStainExists){
              bloodCulture.lab_tests.push(new LabTest("Gram Stain", k));
            }
          }
          else{
            if(gramStainExists){
              bloodCulture.lab_tests = _.filter(bloodCulture.lab_tests, function(lt){
                if(lt.test_name === "Gram Stain" && lt.result === k){
                  return false;
                }
                return true;
              });
            }
          }
        });
      };

      self.isFishTest = function(someTest){
        return _.contains(_.values(self.fishTests), someTest.test_name);
      };

      self.hasFishTest = function(){
        return _.any(bloodCulture.lab_tests, function(lt){
          return self.isFishTest(lt);
        });
      }

      self.initialise = function(){
        if(_.isUndefined(bloodCulture.isolates)){
          bloodCulture.isolates = [];
        }
        else{
          bloodCulture.isolates = _.sortBy(bloodCulture.isolates, function(i){
            return i.aerobic;
          });
        }

        if(!bloodCulture.lab_tests || !bloodCulture.lab_tests.length){
          bloodCulture.lab_tests = [new LabTest("Gram Stain")];
        }

        self.multiGramStain = {};

        _.each(_.values(self.gramStainMeta), function(gm){
          self.multiGramStain[gm] = _.any(bloodCulture.lab_tests, function(lt){
            return lt.test_name === "Gram Stain" && lt.result === gm;
          });
        });

        /*
        * we chunk the gram stains into those with fish tests
        * and those without
        */
        self.gramStainChunkNames = [];
        self.gramStainChunkNames.push(_.keys(self.fishTests).sort())
        self.gramStainChunkNames.push(_.filter(_.keys(self.multiGramStain), function(stain){
          return !self.fishTests[stain];
        }).sort());

        self.updateTests();
      };

      self.initialise();
  };

  return BloodCultureFormHelper;
});
