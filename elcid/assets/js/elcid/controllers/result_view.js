angular.module('opal.controllers').controller('ResultView', function(LabTestResultsView){
      "use strict";
      var vm = this;
      this.filterValue = "";
      this.filter = function(item){
          if(!vm.filterValue){
            return true;
          }

          var nameContains = item.test_name.toLowerCase().indexOf(vm.filterValue.toLowerCase()) > -1
          var resultContains = item.result.toLowerCase().indexOf(vm.filterValue.toLowerCase()) > -1
          return nameContains || resultContains;
      };

      this.getLabTests = function(patient){
        return LabTestResultsView.load(patient.id);
      });


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
