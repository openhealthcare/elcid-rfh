directives.directive("tbSummaryTests", function(InitialPatientTestLoadStatus, TestSummaryLoader){
  "use strict";
  return {
    restrict: 'A',
    scope: true,
    link: function(scope, element, attrs){
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
            TestSummaryLoader.load(attrs.apiUrl, patientId).then(function(result){
              scope.data = result;
            });
        });
      }
    }
  };
});