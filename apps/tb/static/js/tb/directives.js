directives.directive("tbSummaryTests", function(InitialPatientTestLoadStatus, TestSummaryLoader){
  "use strict";
  return {
    restrict: 'A',
    scope: true,
    link: function(scope, element, attrs){
      var patientId = scope.episode.demographics[0].patient_id;
      var patientLoadStatus = new InitialPatientTestLoadStatus(
        scope.episode
      );

      patientLoadStatus.load();
      scope.patientLoadStatus = patientLoadStatus;

      if(!scope.patientLoadStatus.isAbsent()){
        scope.patientLoadStatus.promise.then(function(){
            TestSummaryLoader.load(attrs.apiUrl, patientId).then(function(result){
              scope.data = result;
            });
        });
      }
    }
  };
});