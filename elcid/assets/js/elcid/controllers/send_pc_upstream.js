angular.module("opal.controllers").controller(
    "SendPatientConsultationUpstreamCtrl", function ($scope, $modalInstance, $http, patient, item, callback) {
      $scope._patient = patient;
      $scope.send_upstream = function () {
        $http
          .put("/api/v0.1/send_pc_upstream/" + item.id + "/")
          .then(function() {
            callback().then(function () {
              $modalInstance.close();
            });
          });
      };
      $scope.cancel = function () {
        $modalInstance.close("cancel");
      };
});
