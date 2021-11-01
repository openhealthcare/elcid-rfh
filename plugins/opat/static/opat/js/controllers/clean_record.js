angular.module('opal.controllers').controller('CleanRecordCtrl', function(
	$scope, $http, $q, $window
){
	"use strict";
	var DEFAULT_IGNORES = [
		'id',
		'episode_id',
		'patient_id',
		'consistency_token',
		'created',
		'created_by_id',
		'updated',
		'updated_by_id'
	]
	this.clean = function(subrecord, toIgnore){
		var ignored = toIgnore.concat(DEFAULT_IGNORES)

		_.each(_.keys(subrecord), function(key){
			if(key[0] === '$'){
				return
			}
			if(_.contains(ignored, key)){
				return
			}

			// if its a string, just save an empty
			// string as its the same on a db level
			// but otherwise will break null=False
			// in the db field.
			if(_.isString(subrecord[key])){
				subrecord[key] = "";
			}
			else{
				subrecord[key] = null;
			}
		})
	}
});
