directives.directive("observationGraph", function () {
  "use strict";
  return {
    restrict: 'A',
    scope: {
      data: "=sparkLine",
    },
    link: function (scope, element, attrs) {
      var data = angular.copy(scope.data);
      var dates = _.pluck(scope.data, "date_ordered");
      dates.unshift('date');
      var values = _.pluck(scope.data, "observation_value")
      values.unshift("values");
      var graphParams = {
        bindto: element[0],
        x: 'date',
        data: {
          columns: [dates, values]
        },
        legend: {
          show: false
        },
        axis: {
          x: {type: 'timeseries'},
        },
        size: {
          height: 25,
          width: 150
        }
      };
      setTimeout(function(){
        var chart = c3.generate(graphParams);
      }, 100);
    }
  };
});



directives.directive("sparkLine", function () {
  "use strict";
  return {
    restrict: 'A',
    scope: {
      data: "=sparkLine",
    },
    link: function (scope, element, attrs) {
      var data = angular.copy(scope.data);
      data.unshift("values");
      var graphParams = {
        bindto: element[0],
        data: {
          columns: [data]
        },
        legend: {
          show: false
        },
        tooltip: {
          show: false
        },
        axis: {
          x: {show: false},
          y: {show: false}
        },
        point: {
          show: false,
        },
        size: {
          height: 25,
          width: 150
        }
      };
      setTimeout(function(){
        var chart = c3.generate(graphParams);
      }, 100);
    }
  };
});

directives.directive("populateLabTests", function($http){
  "use strict";
  return {
    restrict: 'A',
    scope: true,
    link: function(scope){
      var patientId = scope.row.demographics[0].patient_id;
      $http.get("/glossapi/v0.1/relevent_lab_test_api/" + patientId + "/").then(function(result){
        scope.data = result.data;

        _.each(scope.data.obs_values, function(data){
          data.graphValues = _.map(data.values, function(someData){
            return parseInt(someData[0]);
          });
        });
      });
    }
  };
});
