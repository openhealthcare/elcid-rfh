angular.module('opal.controllers').controller('ResultView', function(
    $scope, LabTestResults, ngProgressLite, $routeParams
){
    "use strict";
    /*
    * This view is the patient detail lab tests result view.
    * It allows filtering of test names via a filter string
    * This is taken from the url 'test_name' GET param if it exists.
    */
    var vm = this;

    this.labTests = [];
    this.showAll = {};

    this.parseFloat = parseFloat;
    this.Math = window.Math;
    if($routeParams.test_name){
        this.filterString = $routeParams.test_name;
    }

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

    vm.getLabTests($scope.patient);
});
