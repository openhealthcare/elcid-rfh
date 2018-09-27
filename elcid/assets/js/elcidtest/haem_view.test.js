describe('HaemView', function() {
  "use strict";

  var controller;
  var $rootScope;

  beforeEach(function(){
      var $controller;
      module('opal.controllers');
      inject(function($injector){
          $controller = $injector.get('$controller');
          $rootScope = $injector.get('$rootScope');
      });

      var $scope = $rootScope.$new();
      $scope.patient = {episodes: []};
      controller = $controller('HaemView', {$scope: $scope});
  });

  describe("it should order an event based on an episode date hierachy", function(){
      it("should use end as the higest priority", function(){
          var fakeEpisode = {
              end: moment(new Date(2015, 1, 1)),
              start: moment(new Date(2013, 1, 1)),
          };
          var ordering = controller.getEpisodeOrdering(fakeEpisode);
          expect(ordering).toBe(-1422748800);
      });

      it("should use start if no other date is available", function(){
        var fakeEpisode = {
            start: moment(new Date(2015, 1, 1)),
        };
        var ordering = controller.getEpisodeOrdering(fakeEpisode);
        expect(ordering).toBe(-1422748800);
      });
  });
});
