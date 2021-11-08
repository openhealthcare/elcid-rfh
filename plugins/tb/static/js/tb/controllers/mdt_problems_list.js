angular.module('opal.controllers').controller('TBMDTList', function($scope, $http) {
	this.hidden = [];
	this.remove = function(episode_id){
		$http.post("/api/v0.1/tag/" + episode_id + '', {tag: 'mdt_problems'});
		this.hidden.push(episode_id)
	}
});
