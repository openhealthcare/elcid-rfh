angular.module('opal.controllers').controller('TaggingStepCtrl',
  function(scope, step, $http) {
      "use strict";

      var INFECTION_SERVICE = "infection_service";

      scope.categorySlug = INFECTION_SERVICE;

      scope.init = function(){
        scope.value = [];
        scope.tagsList = [];
        scope.editing.tagging = {};
        var url = "/elcid/v0.1/tags_for_category/" + scope.categorySlug + '/';
        $http({cache: true, url: url, method: 'GET'}).then(function(response){
          _.each(scope.editing.tagging, function (value, key) {
            if(value && key !== 'id' && !key.startsWith("_")){
              scope.value.push(scope.metadata.tags[key]);
            }
          });
          _.each(response.data, function(tagSlug){
            scope.tagsList.push(scope.metadata.tags[tagSlug])
          });
        })
      }

      scope.onRemove = function($item, $modal){
        scope.editing.tagging[$modal] = false;
      }

      scope.onSelect = function($item, $modal){
        scope.editing.tagging[$modal] = true;
      }

      scope.init();
  }
);
