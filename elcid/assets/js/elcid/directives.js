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
            if(attrs.getParams){
              var getParams = scope.$eval(attrs.getParams);
              url += '?' + $.param(getParams);
            }
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

directives.directive('fixedHeader', function(){
  return {
    restrict: 'A',
    link: function(scope, $elm, attrs) {
      var panelHeader = $(".panel-heading.patient-detail-heading");
      var counter = 0;
      var adjustHeights = function(){
        var panelHeaderHeight = panelHeader.height();

        // the nav bar collapses at small sizes, accomdate for this.
        var navBar = $("#main-navbar:visible");
        var navBarHeight = 0;
        if(navBar.length){
          navBarHeight = navBar.height();
          panelHeader.css('top', navBarHeight);
        }
        else{
          navBarHeight = $($(".navbar-header")[0]).height();
          panelHeader.css('top', navBarHeight);
        }
        var modifier = panelHeaderHeight + navBarHeight - 30;
        $elm.css('margin-top', modifier);

        // when we're not at the top of the scoll bar
        if(document.documentElement.scrollTop){
          panelHeader.addClass('shrunken');
        }
        else{
          panelHeader.removeClass('shrunken');
        }
        counter += 1;
        if(counter > 20){
          clearInterval(interval)
        }
      }
      var shrinkHeader = function(){
        // when we're slightly down the page add the class
        if(document.documentElement.scrollTop> 100){
          panelHeader.addClass('shrunken');
        }
        else{
          panelHeader.removeClass('shrunken');
        }
      }

      // Angular occassionally populates the header
      // after the directive has loaded, so just
      // keep at it for the firsrt 20 seconds
      var interval = setInterval(adjustHeights, 100);
      $(window).scroll(shrinkHeader);
      $(window).resize(adjustHeights);
    }
  }
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
        printPage(scope.$eval(attrs.printPage))
      });
    }
  }
});


directives.directive('scrollOnClick', function() {
  return {
    restrict: 'A',
    link: function(scope, $elm, attrs) {
      var idToScroll = attrs.target;
      $elm.on('click', function() {
        var $target;
        if (idToScroll) {
          $target = $(idToScroll);
        } else {
          $target = $elm;
        }
          $("html,body").animate({scrollTop: $target.offset().top-100}, "slow");
          return false;
      });
    }
  }
});
