angular.module('opal.controllers').controller('ResultView', function($scope, LabTestResults){
      "use strict";
      var vm = this;
      // lab tests after filtering
      this.labTests = [];
      // lab tests before filtering
      this.originalLabTests = [];

      this.filterValue = "";
      this.filter = function(){
        // filter lab tests so that if its contains in the lab test name
        // we show all of them, otherwise if its in the observation but not
        // the lab test name just show that observation

        var toFilter = angular.copy(vm.originalLabTests);
        if(!vm.filterValue){
          return toFilter;
        }

        var newLabTests = [];

        _.each(toFilter, function(labTest){
          if(labTest.lab_test_type.toLowerCase().indexOf(vm.filterValue.toLowerCase()) > -1){
            newLabTests.push(labTest)
          }
          else{
            var observations = _.filter(labTest.observations, function(observation){
              return observation.test_name.toLowerCase().indexOf(vm.filterValue.toLowerCase()) > -1
            });

            if(observations.length){
              labTest.observations = observations;
              newLabTests.push(labTest);
            }
          }
        });

        return newLabTests;
      };

      this.filterRows = function(){
        this.labTests = vm.filter();
      }

      this.getLabTests = function(patient){
        return LabTestResults.load(patient.id).then(function(result){
          vm.originalLabTests = result;
          vm.labTests = angular.copy(vm.originalLabTests)
        });
      };

      this.labTests = [];
      this.getLabTests($scope.patient);


      // var extractLabTests = function(labTestCollections){
      //     var result = [];
      //     _.each(labTestCollections, function(labTestCollection){
      //       if(labTestCollection && labTestCollection.lab_tests){
      //         result = _.union(result, labTestCollection.lab_tests);
      //       }
      //     });
      //
      //     return result;
      // };
      //
      // this.getLabTests = function(patient){
      //   var result = [];
      //
      //   _.each(patient.episodes, function(episode){
      //     _.each(episode, function(subrecords, subrecordName){
      //       result = _.union(result, extractLabTests(subrecords));
      //
      //       if(subrecordName === 'blood_culture'){
      //         _.each(subrecords, function(subrecord){
      //             result = _.union(result, extractLabTests(subrecord.isolates));
      //         });
      //       }
      //     });
      //   });
      //   result = _.filter(result, function(r){
      //     return r.result !== "Not Done";
      //   });
      //   return _.filter(result, vm.filter)
      // };
});
