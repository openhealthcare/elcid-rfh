angular.module('opal.controllers').controller('ResultView', function(
    $scope, LabTestResults, ngProgressLite, StarObservation
){
    "use strict";
    var vm = this;

    this.labTests = [];
    this.showAll = {};
    this.starObservation = StarObservation;

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

    this.toggleShowAll = function(what){
        vm.showAll[what] = true;
    }

    /*
    * If the view is the result page and the tests have not
    * loaded then load the results.
    *
    * After we've loaded them, cache them.
    */
    $scope.$watch('view', function(){
        if(!_.size(vm.lab_tests) && $scope.view === "test_results"){
            vm.getLabTests($scope.patient);
        }
    })
});
