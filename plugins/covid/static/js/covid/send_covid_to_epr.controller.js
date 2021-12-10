angular.module('opal.controllers').controller(
	'SendCovidToEPR',
	function($scope, $modalInstance, $http, $q, modelApiName, itemId, callBack){
			$scope.send_upstream = function(){
					var url = "/api/v0.1/epr_" + modelApiName + "/" + itemId + "/";
					$http.put(url).then(
							function(response){
								$q.when(callBack()).then(function(){
									$modalInstance.close();
								});
							}
					)
			}

			$scope.cancel = function(){
					$modalInstance.close('cancel');
			}
	}
);
