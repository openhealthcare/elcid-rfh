angular.module('opal.controllers').controller(
	'SendCovidToEPR',
	function($scope, $modalInstance, $http, $q, modelApiName, itemId, callBack, first_name, surname, hospital_number, date_of_birth){
		$scope._patient = {
			demographics: [{
				'first_name': first_name,
				'surname': surname,
				'date_of_birth': date_of_birth,
				'hospital_number': hospital_number
			}]
		}

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
