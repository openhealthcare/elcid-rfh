angular.module('opal.controllers').controller('TBMDTList', function($scope, $http) {
	this.hidden = [];
	this.remove = function(tag_id){
		$http.delete("/api/v0.1/tag/" + tag_id + '/');
		this.hidden.push(tag_id)
	}
});
