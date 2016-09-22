angular.module('opal.services').factory('BloodCultureFormHelper', function(Item){
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
      var gramStainMeta = _.find(metadata.lab_test, function(lt){
        return lt.name === 'gram_stain';
      }).result_choices;

      var fishTests = {
          "Yeast": "QuickFISH",
          "Gram +ve Cocci Cluster": "GPC Staph",
          "Gram +ve Cocci Chains": "GPC Strep",
          "Gram -ve": "GNR"
      };

      self.addAerobic = function(){
        // insert an element between the last aerobic and the
        // first anaerobic
        var firstAnaerobicIndex = _.findIndex(bloodCulture.isolates, function(bc){
          return !bc.aerobic;
        });
        var isolate = {
          aerobic: true,
          lab_tests: [{test_name: "Organism"}]
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
            lab_tests: [{test_name: "Organism"}]
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

      self.updateTests = function(){
        bloodCulture.lab_tests = _.filter(bloodCulture.lab_tests, function(lt){
          return !_.contains(_.values(fishTests), lt.test_name) && lt.test_name !== "Gram Stain";
        });

        _.each(self.multiGramStain, function(v, k){
          if(v){
            bloodCulture.lab_tests.push({
              test_name: fishTests[k],
              result: "Not Done"
            });
            bloodCulture.lab_tests.push({
              test_name: "Gram Stain",
              result: k
            });
          }
        });
      };

      self.isFishTest = function(someTest){
        return _.contains(_.values(fishTests), someTest.test_name);
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
          bloodCulture.lab_tests = [{test_name: "Gram Stain"}];
        }

        self.multiGramStain = {};

        _.each(_.values(gramStainMeta), function(gm){
          self.multiGramStain[gm] = _.any(bloodCulture.lab_tests, function(lt){
            return lt.test_name === "Gram Stain" && lt.result === gm;
          });
        });

        self.fishTestNames = _.values(fishTests);
      };

      self.initialise();
  };

  return BloodCultureFormHelper;
});
