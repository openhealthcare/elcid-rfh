directives.directive("investigationGraph", function () {
  "use strict";
  return {
    restrict: 'A',
    scope: {
      data: "=investigationGraph",
    },
    link: function (scope, element, attrs) {
      var graphParams = {
        bindto: element[0],
        data: {
          columns: [scope.data]
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

directives.directive("populateLabTestView", function($http){
  "use strict";
  return {
    restrict: 'A',
    scope: true,
    link: function(scope){
      var patientId = scope.row.demographics[0].patient_id;
      $http.get("/glossapi/v0.1/lab_test_results_view/" + patientId + "/").then(function(result){
        scope.data = result.data;

        _.each(scope.data.obs_values, function(data){
          data.graphValues = _.map(data.values, function(someData){
            return parseInt(someData[0]);
          });
          data.graphValues.unshift("values");
        });
      });
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
          data.graphValues.unshift("values");
        });
      });
    }
  };
});
