describe('ClinicalAdviceFormTest', function() {
    "use strict";

    var $scope, $httpBackend, $rootScope, $controller;
    var Episode, ctrl, opalTestHelper;
    var mkcontroller;

    var episodedata = {
        id: 1,
        demographics: [ { patient_id: 123 } ]
    }
    var recorddata = {
            'microbiology_input': {
                'name': 'microbiology_input',
                'fields': [
                    {name: 'reason_for_interaction', type: 'string'},
                ]
            }
    };

    beforeEach(function(){

        module('opal.controllers');
        module('opal.test');

        inject(function($injector){
            opalTestHelper = $injector.get('opalTestHelper');
            $httpBackend = $injector.get('$httpBackend');
            $rootScope   = $injector.get('$rootScope');
            $scope       = $rootScope.$new();
            $controller  = $injector.get('$controller');
            Episode      = $injector.get('Episode');
        });

        $scope.episode = new Episode(episodedata);

        mkcontroller = function(){
            ctrl = $controller('ClinicalAdviceForm', {
                $rootScope: $rootScope,
                $scope: $scope,
            });
        };
        $httpBackend.expectGET('/api/v0.1/referencedata/').respond({});
        $httpBackend.expectGET('/api/v0.1/record/').respond(recorddata);
    });

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('initialization', function() {
      it('should setup editing', function() {
          mkcontroller();
          $rootScope.$apply();
          $httpBackend.flush();
          expect(!!ctrl.editing.microbiology_input).toBe(true)
      });

      it('should set chagned to false', function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
        expect(ctrl.changed).toBe(false);
      })
    });

    describe('it should save', function(){
      beforeEach(function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
        ctrl.editing.microbiology_input.reason_for_interaction = "something";
      });

      it('should reset item', function(){
          $httpBackend.expectPOST(
            "/api/v0.1/microbiology_input/",
            {
              reason_for_interaction: "something",
              episode_id: 1
            }
          ).respond({});
          ctrl.save();
          $rootScope.$apply();
          $httpBackend.flush();
          expect(ctrl.editing.microbiology_input.reason_for_interaction).toBe(undefined);
      });

      it('should reset changed', function(){
        $httpBackend.expectPOST(
          "/api/v0.1/microbiology_input/",
          {
            reason_for_interaction: "something",
            episode_id: 1
          }
        ).respond({});
        ctrl.changed = true;
        ctrl.save();
        $rootScope.$apply();
        $httpBackend.flush();
        expect(ctrl.changed).toBe(false);
      });

      it('should always save for the episode that is currently on scope', function(){
        var episode2 = new Episode(opalTestHelper.getEpisodeData());
        $scope.episode = episode2;
        $httpBackend.expectPOST(
          "/api/v0.1/microbiology_input/",
          {"reason_for_interaction":"something","episode_id":123}
        ).respond({reason_for_interaction: "something"});

        ctrl.save();
        $httpBackend.flush();
        $rootScope.$apply();
        expect(_.last($scope.episode.microbiology_input).reason_for_interaction).toBe("something");
      });
    });

    describe('it should notice changes to fields', function(){

      beforeEach(function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
      });

      it('should notice if a field has changed', function(){
        expect(ctrl.changed).toBe(false);
        var mi = {reason_for_interaction: "they had a problem"}
        ctrl.watchMicroFields(mi);
        expect(ctrl.changed).toBe(true);
      });

      it('should ignore changes that to _client, when and initials', function(){
        expect(ctrl.changed).toBe(false);
        var mi = {
          _client: "something",
          when: "something",
          initials: "something",
        }
        ctrl.watchMicroFields(mi);
        expect(ctrl.changed).toBe(false);
      });

      it('should ignore changes that to angular vars', function(){
        expect(ctrl.changed).toBe(false);
        var mi = {
          $$: "something"
        }
        ctrl.watchMicroFields(mi);
        expect(ctrl.changed).toBe(false);
      });

    });

});
