angular
  .module("opal.controllers")
  .controller("ElcidEditTeamsCtrl", function ($scope, $http, $modalInstance, ngProgressLite, episode, Metadata) {
		"use strict";

		$scope.init = function(){
			$scope.episode = episode;
			var loading = true;
			$scope.value = [];
			$scope.tagsList = [];
			$scope.editing = {tagging: episode.tagging[0].makeCopy()}
			var categorySlug = episode.category_name.toLowerCase().replaceAll(" ", "_")
			var url = "/elcid/v0.1/tags_for_category/" + categorySlug + '/';
			$http({cache: true, url: url, method: 'GET'}).then(function(response){
				Metadata.load().then(function(metadata){
					_.each($scope.editing.tagging, function (value, key) {
						if(value && key !== 'id' && !key.startsWith("_")){
							$scope.value.push(metadata.tags[key]);
						}
					});
					_.each(response.data, function(tagSlug){
						$scope.tagsList.push(metadata.tags[tagSlug])
					});
					loading = false;
				})
			})
		}

		$scope.onRemove = function($item, $modal){
			$scope.editing.tagging[$modal] = false;
		}

		$scope.onSelect = function($item, $modal){
			$scope.editing.tagging[$modal] = true;
		}

    //
    // Save the teams.
    //
    $scope.save = function (result) {
      ngProgressLite.set(0);
      ngProgressLite.start();
      episode.tagging[0].save($scope.editing.tagging).then(
        function () {
          ngProgressLite.done();
          $modalInstance.close(result);
        },
        function () {
          ngProgressLite.done();
        }
      );
    };

    $scope.cancel = function () {
      $modalInstance.close("cancel");
    };

		$scope.init();
  });
