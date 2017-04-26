describe('ClinicalAdviceFormTest', function() {
    "use strict";

    var $scope, $httpBackend, $rootScope, $controller;
    var Episode, ctrl;
    var mkcontroller;

    var episodedata = {
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

        inject(function($injector){
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
        $httpBackend.expectGET('/api/v0.1/userprofile/').respond({});
        $httpBackend.expectGET('/api/v0.1/record/').respond(recorddata);
        $httpBackend.expectGET('/api/v0.1/referencedata/').respond({});
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
          expect(!!ctrl.editing).toBe(true)
      });
    });

    describe('it should save', function(){
      beforeEach(function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
        $httpBackend.expectPOST("/api/v0.1/microbiology_input/", {"reason_for_interaction":"something"}).respond({});
      });

      it('should reset item', function(){
          ctrl.editing.reason_for_interaction = "something";
          ctrl.save();
          $rootScope.$apply();
          $httpBackend.flush();
          expect(ctrl.editing.reason_for_interaction).toBe(undefined);
      });


    });

});
