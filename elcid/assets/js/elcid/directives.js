directives.directive("refreshPatient", function(httpBackend){
  return {
    scope: false,
    link: function(scope, element, attrs){
      element.click(function(){
        httpBackend.get("/elicdapi/v0.1/refresh_patient/1/").then(function(patient){
          scope.patient = patient;
        });
      });
    }
  };
});
