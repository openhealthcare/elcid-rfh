angular.module('opal.controllers').controller('EditBloodCultureIsolateCtrl', function(
  $scope,
  formItem, // should have a method of save and delete
  referencedata,
  $modal,
  $modalInstance,
  $q,
  ngProgressLite,
  callBack
){

  $scope.initialize = function(){
    _.extend($scope, referencedata.toLookuplists());
    $scope.formItem = formItem;
  }

  $scope.delete = function(){
    var deferred = $q.defer();
    $modalInstance.close(deferred.promise);
    var deleteModal =  $modal.open({
        templateUrl: '/templates/delete_item_confirmation_modal.html',
        controller: 'GeneralDeleteCtrl',
        resolve: {
            item: function() {
                return $scope.formItem;
            }
        }
    });

    deleteModal.result.then(function(result){
      callBack().then(function(){
        deferred.resolve(result);
      });
    });
  };

  $scope.save = function(){
    ngProgressLite.set(0);
    ngProgressLite.start();
    $scope.formItem.save().then(function(result){
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