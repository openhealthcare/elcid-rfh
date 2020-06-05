directives.directive("bloodCultureResultDisplay", function(BloodCultureLoader){
  return {
    restrict: 'A',
    scope: true,
    link : function($scope, $element){
      $scope.culture_order = [];
      $scope.cultures = {}
      $scope.loadBloodCultures = function(){
        BloodCultureLoader.load($scope.patient.id).then(function(bc_results){
          $scope.culture_order = bc_results.culture_order;
          $scope.cultures = bc_results.cultures;
        });
      }
      $scope.refreshBloodCultures = function(){
        // we need to refresh the parent so that
        // we consistency tokens get updated for
        // form updates
        $scope.refresh();
        $scope.loadBloodCultures();
      };

      $scope.loadBloodCultures();
    }
  };
});

directives.directive('patientApi', function($http, $window){
    "use strict";
    return {
        restrict: 'A',
        link: function(scope, element, attrs){
            var endpoint = attrs.endpoint;
            var target   = attrs.target;

            var url = '/api/v0.1/' + endpoint + '/' + '' + scope.patient.id + '' + '/';

            $http({cache: true, url: url, method: 'GET'}).then(
                function(response){
                    scope[target] = response.data;
                },
                function(){
                    $window.alert('Error loading data from the server')
                }
            )

        }
    }
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


directives.directive("populateLabTests", function(InitialPatientTestLoadStatus, LabTestSummaryLoader){
  "use strict";
  return {
    restrict: 'A',
    scope: true,
    link: function(scope){
      // TODO: this is wrong, well maybe not wrong, but not right
      var episode = scope.row || scope.episode;
      var patientId = episode.demographics[0].patient_id;
      var patientLoadStatus = new InitialPatientTestLoadStatus(
          episode
      );

      // make sure we are using the correct
      // js object scope(ie this)
      patientLoadStatus.load();
      scope.patientLoadStatus = patientLoadStatus;

      if(!scope.patientLoadStatus.isAbsent()){
        scope.patientLoadStatus.promise.then(function(){
            // success
            LabTestSummaryLoader.load(patientId).then(function(result){
              scope.data = result;
            });
        });
      }
    }
  };
});



directives.directive('printPage', function () {
  function closePrint () {
    document.body.removeChild(this.__container__);
  }

  function setPrint () {
    this.contentWindow.__container__ = this;
    this.contentWindow.onbeforeunload = closePrint;
    this.contentWindow.onafterprint = closePrint;
    this.contentWindow.focus(); // Required for IE
    this.contentWindow.print();
  }

  function printPage (sURL) {
    var oHiddFrame = document.createElement("iframe");
    oHiddFrame.onload = setPrint;
    oHiddFrame.style.visibility = "hidden";
    oHiddFrame.style.position = "fixed";
    oHiddFrame.style.right = "0";
    oHiddFrame.style.bottom = "0";
    oHiddFrame.src = sURL;
    document.body.appendChild(oHiddFrame);
  }

  return {
    link: function (scope, element, attrs) {
      element.bind("click", function(){
        printPage(attrs.printPage)
      });
    }
  }
});
