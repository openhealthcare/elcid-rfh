angular.module('opal.controllers').controller('AddEpisodeHelperCtrl',
    function($scope, FieldTranslator, $location, $http, ngProgressLite) {
      "use strict";
      var DATE_FORMAT = 'DD/MM/YYYY';
      this.addEpisode = function(category){
        var toSave = {
            demographics: FieldTranslator.jsToSubrecord(
                $scope.patient.demographics[0].makeCopy(), "demographics"
            )
        }
        delete toSave.demographics._client;

        toSave["category_name"] = category;
        toSave["start"] = moment().format(DATE_FORMAT);
        ngProgressLite.set(0);
        ngProgressLite.start();
        $http.post('/api/v0.1/episode/', toSave).success(function(episode) {
            ngProgressLite.done();
            $location.path('/patient/'+ $scope.patient.id + "/" + episode.id);
        });
      }
      this.hasEpisodeCategory = function(category){
        return !!_.findWhere($scope.patient.episodes, {category_name: category});
      }
});