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
            if (attrs.patientId){
                var patient_id = scope.$eval(attrs.patientId);
            }else{
                var patient_id = scope.patient.id;
            }
            var url = '/api/v0.1/' + endpoint + '/' + '' + patient_id + '' + '/';
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


directives.directive("populateLabTests", function(LabTestSummaryLoader){
  "use strict";
  return {
    restrict: 'A',
    scope: true,
    link: function(scope){
      // TODO: this is wrong, well maybe not wrong, but not right
      var episode = scope.row || scope.episode;
      var patientId = episode.demographics[0].patient_id;

      LabTestSummaryLoader.load(patientId).then(function(result){
        scope.data = result;
      });
    }
  };
});

directives.directive('fixedHeader', function(){
  return {
    restrict: 'A',
    link: function(scope, $elm, attrs) {
      var panelHeader = $(".panel-heading.patient-detail-heading");
      var panelBody = $(".panel.panel-primary.panel-container.patient-detail > .panel-body");

      var modifier = 0;
      var adjustHeights = function(){
        var navBar = $(".navbar.navbar-default.navbar-primary.navbar-fixed-top");
        if(navBar.length){
          navBarHeight = $(navBar[0]).height()
          if(navBarHeight > 52){
            modifier = navBarHeight - 52;
          }
          else{
            modifier = 0;
          }
        }
        panelHeader.css("margin-top", modifier);
        shrinkHeader();
      }

      var shrinkHeader = function(){
        var panelHeaderHeight = panelHeader.height() + 22 + modifier;
        panelHeader.css("position", "fixed");
        panelBody.css('margin-top', panelHeaderHeight)
        // when we're slightly down the page add the class
        if(document.documentElement.scrollTop > 150){
          panelHeader.addClass('shrunken');
        }
        else{
          panelHeader.removeClass('shrunken');
        }
      }
      setTimeout(adjustHeights, 20);
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
            var offset = attrs.offset
            $elm.on('click', function() {
                var $target;
                if (idToScroll) {
                    $target = $(idToScroll);
                } else {
                    $target = $elm;
                }
                if (offset){
                    offset = parseInt(offset);
                } else {
                    offset = 100
                }
                $("html,body").animate({scrollTop: $target.offset().top-offset}, "slow");
                return false;
            });
        }
    }
});

directives.directive('labNumberString', function(){
    return {
        // require: "ngModel",
        scope: true,
        template: "[[text]]<br/><span ng-repeat=\"lab_number in lab_numbers\"><a class=\"orange-link pointer\" ng-click=\"open_modal('LabDetailModalCtrl', '/templates/lab/lab_detail_modal.html', {'lab_number': lab_number} )\">[[ lab_number ]]</a> </span>",
        link: function(scope, element, attrs){
            var text = scope.$eval(attrs.text);
            var regexp = /[0-9]+[LK][0-9]+/g;

            scope.text = text;
            matches = text.match(regexp);
            scope.lab_numbers = _.map(matches, function(x){ return x.replace(/^0+/, '') });
        }
    }

})
