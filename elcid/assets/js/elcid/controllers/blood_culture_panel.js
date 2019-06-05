angular.module('opal.controllers').controller('BloodCulturePanelCtrl', function(
  $rootScope, $scope, $modal, $http, $q
) {
  /*
  * open a panel when the user clicks on it and close and refresh when they are done
  */
  const ctrl = "EditBloodCultureIsolateCtrl";
  const templateUrl = "/templates/blood_culture_isolate_form.html"
  var self = this;

  this.open = function(bcs, item){
    $rootScope.state = 'modal';
    var callBack = function(){
      return self.refresh(bcs);
    }
    var modal_opts = {
        backdrop: 'static',
        templateUrl: templateUrl,
        controller: ctrl,
        resolve: {
            item: function() { return item; },
            blood_culture_set: function(){ return bcs; },
            episode: function() { return $scope.episode; },
            metadata: function(Metadata) { return Metadata.load(); },
            referencedata: function(Referencedata){ return Referencedata.load(); },
            callBack: function(){
              return callBack
            }
        }
    }
    var modal = $modal.open(modal_opts);
    modal.result.then(result => {
      $rootScope.state = 'normal';
    });
  };

  this.refresh = function(bcs){
    var deferred = $q.defer();
    $http.get("/api/v0.1/blood_culture_set/" + bcs.id + "/").then(result => {
      var bcs_idx = _.findIndex($scope.patient.blood_culture_set, {id: bcs.id})
      $scope.patient.blood_culture_set[bcs_idx].isolates = result.data.isolates;
      deferred.resolve();
    })

    return deferred.promise;
  };
});