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

directives.directive("upstreamBloodCultureResultDisplay", function(
  UpstreamBloodCultureLoader, InitialPatientTestLoadStatus
){
  return {
    restrict: 'A',
    scope: true,
    link : function(scope, $element){
      scope.culture_order = [];
      scope.cultures = {}
      scope.patientLoadStatus = new InitialPatientTestLoadStatus(scope.patient);
      scope.patientLoadStatus.load();

      scope.loadBloodCultures = function(){
        UpstreamBloodCultureLoader.load(scope.patient.id).then(function(bc_results){
          scope.bc_results = bc_results;
        });
      }

      if(!scope.patientLoadStatus.isAbsent()){
        scope.patientLoadStatus.promise.then(function(){
          scope.loadBloodCultures();
        });
      }
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

directives.directive('checkboxMultiSelect', function($parse){
  /*
  * Takes in an array which we're saving to and a list
  * of options.
  *
  * input:
  *    checkboxMultiSelect: The list we're adding/removing from
  *    options: The checkbox options available
  *
  * exposes:
  *    checkbox: an object of {value: boolean}
  *
  */
  "use strict";
  return {
    scope: true,
    link: function(scope, element, attrs){
      // if the parent variable has not been defined as an empty array yet then set it
      var getter = $parse(attrs.checkboxMultiSelect)
      if(!getter(scope.$parent)){
        var checkboxMultiSelect = [];
        getter.assign(scope.$parent, checkboxMultiSelect);
        scope.checkboxMultiSelect = checkboxMultiSelect;
      }
      else{
        scope.checkboxMultiSelect = getter(scope);
      }

      scope.options = $parse(attrs.options)(scope);
      scope.checkbox = {};

      var remove = function(option){
        if(contains(option)){
          var index = scope.checkboxMultiSelect.indexOf(option);
          scope.checkboxMultiSelect.splice(index, 1);
        }
      }

      var add = function(option){
        if(!contains(option)){
          scope.checkboxMultiSelect.push(option);
        }
      }

      var contains = function(option){
        return scope.checkboxMultiSelect.indexOf(option) !== -1;
      };

      scope.updatecheckboxMultiSelect = () => {
        // updates checkboxMultiSelect based on checkbox
        scope.options.forEach(option => {
          if(scope.checkbox[option]){
            add(option);
          }
          else{
            remove(option);
          }
        });
      }

      var updateCheckbox = () =>{
        // updates checkbox based on checkboxMultiSelect
        scope.options.forEach(option => {
          scope.checkbox[option] = contains(option);
        });
      }

      updateCheckbox();
    }
  }
});
