angular.module('opal.controllers').controller('ResultView', function($scope, LabTestResults){
      "use strict";
      var vm = this;
      // lab tests after filtering
      this.labTests = [];
      // lab tests before filtering
      this.originalLabTests = [];

      this.filterValue = "";

      this.filter = function(someTag){
        this.currentTag = someTag;
        if(someTag === 'ALL'){
          this.labTests = this.originalLabTests;
        }
        else{
          this.labTests = _.filter(vm.originalLabTests, function(labTest){
            return _.filter(labTest.tags, function(tag){
              return tag == someTag
            }).length;
          });
        }
      }

      this.getLabTests = function(patient){
        return LabTestResults.load(patient.id).then(function(result){
          vm.originalLabTests = result.tests;
          var tags = result.tags;
          tags.unshift("ALL");
          vm.currentTag = "ALL";
          vm.tags = result.tags;
          vm.labTests = angular.copy(vm.originalLabTests)
        });
      };

      this.labTests = [];
      this.getLabTests($scope.patient);
});
