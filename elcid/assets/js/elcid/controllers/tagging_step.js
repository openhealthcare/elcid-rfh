angular.module('opal.controllers').controller('TaggingStepCtrl',
  function(scope, step, $http) {
      "use strict";

      var INFECTION_SERVICE = "infection_service";
      var RNOH = "rnoh"

      scope.categorySlug = INFECTION_SERVICE

      scope.init = function(){
        scope.value = [];
        scope.tagsList = [];
        scope.editing.tagging = {};
        var url = "/elcid/v0.1/tags_for_category/" + scope.categorySlug + '/';
        $http({cache: true, url: url, method: 'GET'}).then(function(response){
          _.each(scope.editing.tagging, function (value, key) {
            if(value && key !== 'id' && !key.startsWith("_")){
              scope.value.push(metadata.tags[key]);
            }
          });
          _.each(response.data, function(tagSlug){
            scope.tagsList.push(metadata.tags[tagSlug])
          });
          loading = false;
        })
      }

      scope.onRemove = function($item, $modal){
        scope.editing.tagging[$modal] = false;
      }

      scope.onSelect = function($item, $modal){
        scope.editing.tagging[$modal] = true;
      }

      scope.$watch('editing.location.hospital', function(){
        if(scope.editing.location.hospital === 'RNOH'){
          if(scope.categorySlug !== RNOH){
            scope.categorySlug = RNOH;
            scope.init();
          }
        }
        else{
          if(scope.categorySlug !== INFECTION_SERVICE){
            scope.categorySlug = INFECTION_SERVICE;
            scope.init();
          }
        }
      });

      scope.init();
  }
);
