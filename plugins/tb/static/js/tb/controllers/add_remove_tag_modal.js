angular
  .module("opal.controllers")
  .controller(
    "AddRemoveTagCtrl",
    function (
      $scope,
      ngProgressLite,
			$modalInstance,
      episode,
      tagName,
      tagDisplayName,
      addTag
    ) {
      "use strict";
      $scope.episode = episode;
      $scope.tagName = tagName;
      $scope.tagDisplayName = tagDisplayName;
      $scope.demographics = $scope.episode.demographics[0];
      $scope.editingName = $scope.demographics.first_name + " " + $scope.demographics.surname;
      $scope.addTag = addTag;

      var tagging = {};
      if (episode.tagging.length) {
        tagging = episode.tagging[0].makeCopy();
      }

			$scope.cancel = function(){
				$modalInstance.close();
			}

      $scope.save = function () {
        ngProgressLite.set(0);
        ngProgressLite.start();
        if ($scope.addTag) {
          tagging[tagName] = true;
        } else {
          tagging[tagName] = false;
        }

        episode.tagging[0].save(tagging).then(
          function () {
            ngProgressLite.done();
            $modalInstance.close();
          },
          function () {
            ngProgressLite.done();
            $modalInstance.close();
          }
        );
      };
    }
  );
