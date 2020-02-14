angular.module('opal.controllers').controller('ResultView', function(
    $scope, LabTestResults, ngProgressLite
){
    "use strict";
    var vm = this;

    this.labTests = [];

    this.parseFloat = parseFloat;
    this.Math = window.Math;

    this.splitObservation = function(observation){
      if(observation){
        return observation.split('~');
      }
      return [];
    }

    this.isNumber = _.isNumber;

    this.isPopulated = function(observation){
        if(_.isUndefined(observation)){
            return false;
        }

        if(_.isNumber(observation)){
            return true;
        }

        return observation.replace('-', '').trim().length;
    }

    this.show = function(name){
        if(!vm.filterString){
            return true
        }
        return name.toLowerCase().indexOf(vm.filterString.toLowerCase()) !== -1
    }

    this.getLabTests = function(patient){
        ngProgressLite.set(0);
        ngProgressLite.start();

        return LabTestResults.load(patient.id).then(function(result){

            vm.test_order = result.test_order;
            vm.lab_tests   = result.tests
            ngProgressLite.done();

        });
    };

    vm.getLabTests($scope.patient);
});
