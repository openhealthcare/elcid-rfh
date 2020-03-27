angular.module('opal.controllers').controller('GeneralEditCtrl', function(
  $scope,
  $rootScope,
  formItem, // should have a method of save and delete
  referencedata,
  $modal,
  $modalInstance,
  $q,
  ngProgressLite,
  callBack
){

  $scope.initialize = function(){
    $rootScope.state = 'modal';
    _.extend($scope, referencedata.toLookuplists());
    $scope.formItem = formItem;
  }

  $scope.editingMode = function(){
    return !$scope.formItem.isNew;
  }

  $scope.close = function(result){
    $q.when(callBack()).then(function(){
      ngProgressLite.done();
      $rootScope.state = 'normal';
      $modalInstance.close(result);
    });
  }

  $scope.delete = function(){
    var deferred = $q.defer()
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
      $scope.close(result);
    });
  };

  $scope.save = function(){
    ngProgressLite.set(0);
    ngProgressLite.start();
    $scope.formItem.save().then(function(result){
      $scope.close(result);
    });
  }

  $scope.cancel = function() {
    $modalInstance.close('cancel');
  }

  $scope.initialize();
});