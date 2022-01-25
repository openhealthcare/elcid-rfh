angular.module('opal.controllers').controller('ResultView', function(
    $scope, LabTestResults, ngProgressLite
){
    "use strict";
    var vm = this;

    this.labTests = [];
    this.departments = [];
    this.showAll = {};
    this.checkedDepartments = {}

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

    this.includes = function(string1, string2){
        // case insensitive check, does string1 exist in string2
        return string2.toLowerCase().indexOf(string1.toLowerCase()) !== -1
    }

    this.show = function(name){
        var toShow = true
        if(vm.filterString && !this.includes(name, vm.filterString)){
            toShow = false;
        }

        if(toShow && _.any(_.values(vm.checkedDepartments))){
            var labTest = vm.lab_tests[name];
            toShow = vm.checkedDepartments[labTest.department]
        }
        return toShow;
    }

    this.getLabTests = function(patient){
        ngProgressLite.set(0);
        ngProgressLite.start();

        return LabTestResults.load(patient.id).then(function(result){

            vm.test_order = result.test_order;
            vm.lab_tests   = result.tests;
            vm.departments = result.departments;
            ngProgressLite.done();

        });
    };

    this.toggleShowAll = function(what){
        vm.showAll[what] = true;
    }

    vm.getLabTests($scope.patient);
});
