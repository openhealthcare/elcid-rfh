angular.module('opal.controllers').controller('TagHelper', function($scope, $http) {
	"use strict";
	this.hidden = [];

	this.changeTag = function(episode, tag_name, value){
		var tagItem = episode.tagging[0]
		var tagCopy = tagItem.makeCopy();
		tagCopy[tag_name] = value;
		return tagItem.save(tagCopy).then(function(){
			// We need to do this because mdt_problems is not
			// a traditional tagged patient list, make
			// copy does not appropriately update the episode.tagging
			// object
			tagItem[tag_name] = value;
		});
	}

	this.addTag = function(episode, tag_name){
		return this.changeTag(episode, tag_name, true);
	}
	this.removeTag = function(episode, tag_name){
		return this.changeTag(episode, tag_name, false);
	}
});
