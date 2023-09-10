angular.module('opal.controllers').controller('BloodCulturePanelCtrl', function(
  $scope, $modal, $http, $q, BloodCultureIsolate
) {
  "use strict";
  /*
  * open a panel when the user clicks on it and close and refresh when they are done
  */
  var ctrl = "GeneralEditCtrl";
  var templateUrl = "/templates/blood_culture_isolate_form.html"
  var self = this;

  this.open = function(blood_culture_set, isolate){
    var isolateForm;
    var callBack = function(){
      return self.refresh(blood_culture_set);
    }
    // isolate is undefined if its a new isolate
    isolateForm =  new BloodCultureIsolate(blood_culture_set, isolate);
    var modal_opts = {
        backdrop: 'static',
        templateUrl: templateUrl,
        controller: ctrl,
        resolve: {
            formItem: function() { return isolateForm; },
            episode: function() { return $scope.episode; },
            metadata: function(Metadata) { return Metadata.load(); },
            referencedata: function(Referencedata){ return Referencedata.load(); },
            callBack: function(){
              return callBack
            }
        }
    }
    var modal = $modal.open(modal_opts);
  };

  this.refresh = function(bcs){
    var deferred = $q.defer();
    $http.get("/api/v0.1/blood_culture_set/" + bcs.id + "/").then(function(result){
      var bcs_idx = _.findIndex($scope.patient.blood_culture_set, {id: bcs.id})
      // when we update isolates we update the fields the previous_mrn, updated*
      // fields on the set.
      $scope.patient.blood_culture_set[bcs_idx].isolates = result.data.isolates;
      $scope.patient.blood_culture_set[bcs_idx].previous_mrn = result.data.previous_mrn;
      $scope.patient.blood_culture_set[bcs_idx].updated = result.data.updated;
      $scope.patient.blood_culture_set[bcs_idx].updated_by_id = result.data.updated_by_id;
      deferred.resolve();
    })

    return deferred.promise;
  };
});
