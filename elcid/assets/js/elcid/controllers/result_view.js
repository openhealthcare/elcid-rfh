angular.module('opal.controllers').controller('ResultView', function($scope, LabTestResults, ObservationDetail){
      "use strict";
      var vm = this;
      // lab tests after filtering
      this.labTests = [];
      // lab tests before filtering
      this.originalLabTests = [];
      this.observationDetail = {};

      this.filterValue = "";

      this.shownObservations = [];

      this.showObservation = function(labTest, observationName){
        this.getObservationDetail(labTest, observationName);
        if(this.isShownObservation(observationName)){
          this.shownObservations = _.without(
            this.shownObservations, observationName
          );
        }
        else{
          this.shownObservations.push(observationName);
        }
      };

      this.isShownObservation = function(observationName){
        return _.contains(this.shownObservations, observationName);
      }

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

      this.trendChange = function(labTest, observationName){
        /*
          tells us with the latest observation value
          is going up or down compared to the previous
          return -1 if its going down, 1 if its going up
          0 if neither or unknown.
        */

        var observationDateRange = labTest.observation_date_range;

        if(observationDateRange.length < 2){
          return 0
        }
        var mostRecent = labTest.by_observations[observationName][observationDateRange[0]].observation_value;
        var nextRecent = labTest.by_observations[observationName][observationDateRange[1]].observation_value;

        if(isNaN(mostRecent) || isNaN(nextRecent)){
          return 0
        }
        var roundedMostRecent = Math.round(mostRecent * 100)/100;
        var roundedNextRecent = Math.round(nextRecent * 100)/100;

        if(roundedMostRecent < roundedNextRecent){
          return -1;
        }
        if(roundedMostRecent === roundedNextRecent){
          return 0;
        }

        return 1;
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

      this.getObservationDetail = function(labTest, observationName){
        if(_.contains(vm.observationDetail, observationName)){
          return;
        }

        var apiName = labTest.observation_metadata[observationName].api_name;

        vm.observationDetail[observationName] = [];

        // _.each(vm.originalLabTests, function())
        ObservationDetail.load(apiName).then(function(detail){
          vm.observationDetail[observationName] = detail.observations;
        });
      };

      this.labTests = [];
      this.getLabTests($scope.patient);
});
