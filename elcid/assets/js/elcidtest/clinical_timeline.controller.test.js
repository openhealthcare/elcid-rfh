describe('ClinicalAdviceFormTest', function() {
    "use strict";

    var $scope, $httpBackend, $rootScope, $controller;
    var Episode, ctrl, opalTestHelper;
    var mkcontroller, $modal;

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
            $modal      = $injector.get('$modal');
        });

        $scope.patient = opalTestHelper.newPatient($rootScope);
        $scope.episode = $scope.patient.episodes[0];

        mkcontroller = function(){
            ctrl = $controller('ClinicalTimeline', {
                $rootScope: $rootScope,
                $scope: $scope,
                $modal: $modal
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
      it('should setup the form item', function() {
          mkcontroller();
          $rootScope.$apply();
          $httpBackend.flush();
          expect(!!ctrl.formItem).toBe(true)
      });

      it('should set changed to false', function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
        expect(ctrl.changed).toBe(false);
      });

      it('should set changed to false when reviewing the initial clinical advice', function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
        ctrl.watchMicroFields(ctrl.getClinicalAdviceFormObject().editing);
        expect(ctrl.changed).toBe(false);
      });

      it('should set changed to true if the clinical advice has changed', function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
        var clinicalAdviceForm = ctrl.getClinicalAdviceFormObject();
        clinicalAdviceForm.editing.clinical_discussion = "clinical discussion"
        ctrl.watchMicroFields(clinicalAdviceForm);
        expect(ctrl.changed).toBe(true);
      });


      it('should set clinical advice to empty if there are no clinical advice', function(){
        $scope.episode.microbiology_input = [];
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
        expect(ctrl.clinicalAdvice).toEqual([]);
      });

      it("should combine clinical advice from multiple episodes in date order", function(){
        var episodeData = opalTestHelper.getEpisodeData()
        episodeData["id"] = 124;
        $scope.patient.episodes.push(opalTestHelper.newEpisode(episodeData));
        var advice1 = {
          reason_for_interaction: "first date",
          initials: "TTT",
          when: moment(new Date(2018, 12, 1))
        }

        var advice2 = {
          reason_for_interaction: "middle date",
          initials: "TTT",
          when: moment(new Date(2018, 13, 1))
        }

        var advice3 = {
          reason_for_interaction: "last date",
          initials: "TTT",
          when: moment(new Date(2018, 14, 1))
        }
        $scope.patient.episodes[0].microbiology_input = [
          advice1, advice3
        ];

        $scope.patient.episodes[1].microbiology_input = [
          advice2
        ];
        mkcontroller();
        $httpBackend.flush();
        expect(ctrl.clinicalAdvice).toEqual(
          [advice3, advice2, advice1]
        )
      });
    });

    describe('hasIcuOrObservation', function(){
      var item;
      beforeEach(function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
      });

      it('should return true if the icu round is populated', function(){
        item = {
          reason_for_interaction: "ICU round",
          micro_input_icu_round_relation: {
            icu_round: {
              inotropic: true
            },
            observation: {}
          }
        }
        expect(ctrl.hasIcuOrObservation(item)).toBe(true);
      });

      it('should return true if the observation is populated', function(){
        item = {
          reason_for_interaction: "ICU round",
          micro_input_icu_round_relation: {
            icu_round: {},
            observation: {temperature: 38.5}
          }
        }
        expect(ctrl.hasIcuOrObservation(item)).toBe(true);
      });

      it('should return false if reason for interaction is not ICU round', function(){
        item = {
          reason_for_interaction: "Other",
          micro_input_icu_round_relation: {
            icu_round: {},
            observation: {temperature: 38.5}
          }
        }
        expect(ctrl.hasIcuOrObservation(item)).toBe(false);
      });

      it('should return false if the icu round and observation are not populated', function(){
        item = {
          reason_for_interaction: "ICU round",
          micro_input_icu_round_relation: {
            icu_round: {},
            observation: {}
          }
        }
        expect(ctrl.hasIcuOrObservation(item)).toBe(false);
      });
    });

    describe('it should save', function(){
      beforeEach(function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
      });

      it('should reset item', function(){
        ctrl.changed = true
        spyOn(ctrl.formItem, "save").and.returnValue({
          then: function(x){ x() }
        });
        spyOn(ctrl, "getClinicalAdviceFormObject");
        spyOn(ctrl, "getClinicalAdvice");
        ctrl.save();
        $rootScope.$apply();
        expect(ctrl.getClinicalAdviceFormObject).toHaveBeenCalledWith();
        expect(ctrl.getClinicalAdvice).toHaveBeenCalledWith();
        expect(ctrl.changed).toBe(false);
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
          initials: "something"
        }
        ctrl.watchMicroFields(mi);
        expect(ctrl.changed).toBe(false);
      });
    });

    describe("editItem", function(){
      var fakeItem, clinicalAdvice;

      beforeEach(function(){
        mkcontroller();
        $rootScope.$apply();
        $httpBackend.flush();
        spyOn($modal, "open");
        fakeItem = {fake: "item"};
        clinicalAdvice = "clinicalAdvice"
        spyOn(ctrl, "getClinicalAdviceFormObject").and.returnValue(clinicalAdvice);
        spyOn(ctrl, "getClinicalAdvice");
      });

      it("open the modal with the correct arguments", function(){
        ctrl.editItem(fakeItem);
        var callArgs = $modal.open.calls.allArgs();
        expect(callArgs.length).toBe(1);
        var call = callArgs[0][0];
        expect(call.backdrop).toBe('static');
        expect(call.templateUrl).toBe("/templates/modals/microbiology_input.html/");
        expect(call.controller).toBe("GeneralEditCtrl");
        expect(call.resolve.formItem()).toBe(clinicalAdvice);
        expect(ctrl.getClinicalAdvice.calls.any()).toBe(false);
      });

      it("should reload the clinical advice as a callback", function(){
        ctrl.editItem(fakeItem);
        var callArgs = $modal.open.calls.allArgs();
        var call = callArgs[0][0];
        var result = call.resolve.callBack()();
        expect(ctrl.getClinicalAdvice.calls.any()).toBe(true);
      });
    })

});
