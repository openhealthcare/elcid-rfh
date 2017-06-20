directives.directive("observationGraph", function (toMomentFilter) {
  "use strict";
  return {
    restrict: 'A',
    scope: {
      observations: "=observationGraph",
      observationRange: "=observationRange",
      observationName:"=observationName"
    },
    link: function (scope, element, attrs) {
      var observations = angular.copy(_.values(scope.observations));
      observations = _.map(observations, function(observation){
        var dt = observation["datetime_ordered"];
        observation["datetime_ordered"] = toMomentFilter(dt).toDate()
        return observation;
      });

      observations = _.sortBy(observations, function(observation){
        return observation["datetime_ordered"];
      });

      var dates = _.pluck(observations, "datetime_ordered");
      var values = _.pluck(observations, "observation_value");

      dates.unshift('Date');
      values.unshift(scope.observationName);

      var graphParams = {
        bindto: element[0],
        data: {
          x: "Date",
          y: scope.observationName,
          xFormat: '%d/%m/%Y %H:%M:%S',
          columns: [dates, values]
        },
        legend: {
          show: false
        },
        subchart: {
           show: true
        },
        axis: {
          x: {
            type: 'timeseries',
            tick: {
              format: '%d/%m/%Y %H:%M:%S'
            }
          },
          y: {
            tick: {
              count: 5,
              format: d3.format('.2f')
            }
          }
        }
      };

      var threeMonthsAgo = moment().subtract(3, "M");

      if(moment(observations[0].datetime_ordered).diff(threeMonthsAgo) < 0){
        graphParams.axis.x.extent = [threeMonthsAgo.toDate(), new Date()];
      }

      if(scope.observationRange){
        graphParams.regions = [
          {
            axis: 'y',
            end: scope.observationRange.min,
            class: 'too-low'
          },
          {
            axis: 'y',
            start: scope.observationRange.max,
            class: 'too-high'
          }
        ];
      }
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
