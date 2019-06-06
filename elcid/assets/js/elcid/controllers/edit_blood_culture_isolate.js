angular.module('opal.controllers').controller('EditBloodCultureIsolateCtrl', function(
  $scope,
  item,
  blood_culture_set,
  referencedata,
  $modal,
  $modalInstance,
  BloodCultureIsolate,
  $q,
  ngProgressLite,
  callBack
){

  $scope.initialize = function(){
    _.extend($scope, referencedata.toLookuplists());

    // lists should be alphabetical but with
    // Negative always as the last result
    // if the list contains negative
    var lists = [
      "gramstainoutcome_list",
      "quickfishoutcome_list",
      "gpcstaphoutcome_list",
      "gpcstrepoutcome_list"
    ]

    _.each(lists, list => {
      var removed = _.without($scope[list], 'Negative');
      if(removed.length !== $scope[list].length){
        removed.push("Negative");
        $scope[list] = removed;
      }
    });


    // are we editing or creating
    if(item){
      $scope.isNew = false;
      $scope.isolate = new BloodCultureIsolate(blood_culture_set, item)
    }
    else{
      $scope.isNew = true;
      $scope.isolate = new BloodCultureIsolate(blood_culture_set);
    }
  }

  $scope.delete = function(){
    var deferred = $q.defer();
    $modalInstance.close(deferred.promise);
    var deleteModal =  $modal.open({
        templateUrl: '/templates/delete_item_confirmation_modal.html',
        controller: 'DeleteBloodCultureIsolateCtrl',
        resolve: {
            item: function() {
                return $scope.isolate;
            }
        }
    });

    deleteModal.result.then(function(result){
      deferred.resolve(result)
    });
  };

  $scope.save = function(){
    ngProgressLite.set(0);
    ngProgressLite.start();
    $scope.isolate.save().then(function(result){
      callBack().then(function(){
        ngProgressLite.done();
        $modalInstance.close(result);
      });
    });
  }

  $scope.cancel = function() {
    $modalInstance.close('cancel');
  }

  $scope.initialize();
});