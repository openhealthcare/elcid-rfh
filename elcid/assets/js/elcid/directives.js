directives.directive("investigationGraph", function () {
  "use strict";
  return {
    restrict: 'A',
    scope: {
      data: "=investigationGraph"
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
          width: 50
        }
      };
      setTimeout(function(){
        var chart = c3.generate(graphParams);
      }, 100);
    }
  };
});
