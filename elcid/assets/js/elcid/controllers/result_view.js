angular.module('opal.controllers').controller('ResultView', function(
  $scope, LabTestResults, ObservationDetail, LabTestJsonDump
){
      "use strict";
      var vm = this;
      // lab tests after filtering
      this.labTests = [];
      // lab tests before filtering
      this.originalLabTests = [];
      this.observationDetail = {};


      this.shownObservations = {};

      this.showObservation = function(labTest, observationName){
        this.getObservationDetail(labTest, observationName);
        if(this.isShownObservation(labTest, observationName)){
          this.shownObservations[labTest.lab_test_type] = _.without(
            this.shownObservations[labTest.lab_test_type], observationName
          );
        }
        else{
          if(!(labTest.lab_test_type in this.shownObservations)){
              this.shownObservations[labTest.lab_test_type] = [];
          };
          this.shownObservations[labTest.lab_test_type].push(observationName);
        }
      };

      this.isShownObservation = function(labTest, observationName){
        if(labTest.lab_test_type in this.shownObservations){
          if(_.contains(this.shownObservations[labTest.lab_test_type], observationName)){
            return true;
          }
        }
        return false;
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
        var obvsLength = observationDateRange.length;

        if(obvsLength < 2){
          return 0
        }

        var recentObservation = labTest.by_observations[observationName][observationDateRange[obvsLength - 1]];
        var nextObservation = labTest.by_observations[observationName][observationDateRange[obvsLength - 2]];

        if(!recentObservation){
          return 0;
        }

        if(!nextObservation){
          return 0;
        }

        var mostRecent = recentObservation.observation_value;
        var nextRecent = nextObservation.observation_value;

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

      function syntaxHighlight(json) {
          if (typeof json != 'string') {
               json = JSON.stringify(json, undefined, 2);
          }
          json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
          return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
              var cls = 'number';
              if (/^"/.test(match)) {
                  if (/:$/.test(match)) {
                      cls = 'key';
                  } else {
                      cls = 'string';
                  }
              } else if (/true|false/.test(match)) {
                  cls = 'boolean';
              } else if (/null/.test(match)) {
                  cls = 'null';
              }
              return '<span class="' + cls + '">' + match + '</span>';
          });
      }
      this.getJsonDump = function(patient){
        LabTestJsonDump.load(patient.id).then(function(result){
          vm.pprintedJson = syntaxHighlight(result);
        });
      };

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
        if(labTest.lab_test_type in vm.observationDetail){
          if(_.contains(vm.observationDetail[labTest.lab_test_type], observationName)){
            return;;
          }
        }
        else{
          vm.observationDetail[labTest.lab_test_type] = {};
        }

        var apiName = labTest.observation_metadata[observationName].api_name;

        vm.observationDetail[observationName] = [];

        // _.each(vm.originalLabTests, function())
        ObservationDetail.load(labTest.api_name, apiName).then(function(detail){
          vm.observationDetail[labTest.lab_test_type][observationName] = detail.observations;
        });
      };

      this.labTests = [];
      this.getLabTests($scope.patient);
      this.getJsonDump($scope.patient);
});
