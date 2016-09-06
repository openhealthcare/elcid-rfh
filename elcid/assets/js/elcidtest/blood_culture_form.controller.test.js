describe('BloodCultureFormCtrlTest', function() {
    "use strict";

    var fakeItem, $scope, $q, controller, fakeModalInstance;

    beforeEach(function(){

        module('opal.controllers', function($provide) {
            $provide.value('UserProfile', function(){ return profile; });
        });
        var $rootScope;
        var $controller;
        var Episode;
        var Item;
        var $cookieStore;
        var $timeout;
        var ngProgressLite;

        inject(function($injector){
            $rootScope   = $injector.get('$rootScope');
            $scope       = $rootScope.$new();
            $controller  = $injector.get('$controller');
            $q           = $injector.get('$q');
            ngProgressLite = $injector.get('ngProgressLite');
            $timeout       = $injector.get('$timeout');
            $cookieStore   = $injector.get('$cookieStore');
            Episode      = $injector.get('Episode');
            Item         = $injector.get('Item');
        });

        $rootScope.fields = {};
        var episode =  new Episode({demographics: [{patient_id: 1}]});
        fakeModalInstance = {
            close: function(){
                // do nothing
            }
        };

        fakeItem = {
            save: function(){
                // do nothing
            },
            makeCopy: function(){
                return {};
            },
            episode: episode
        };

        controller = $controller('BloodCultureFormCtrl', {
            $scope        : $scope,
            $cookieStore  : $cookieStore,
            $timeout      : $timeout,
            $modalInstance: fakeModalInstance,
            item          : fakeItem,
            referencedata : {toLookuplists: function(){ return {} }},
            profile       : {},
            metadata      : {},
            episode       : episode,
            ngProgressLite: ngProgressLite,
        });
    });


    describe('it should inherit from EditItem', function(){
        it('should have a save method that saves', function(){
          $scope.editing.blood_culture = [{
            lab_number: "1"
          }];
          $scope.$digest();
          var callArgs;
          var deferred = $q.defer();
          spyOn(fakeItem, 'save').and.callFake(function() {
              return deferred.promise;
          });
          $scope.save('save');
          deferred.resolve("episode returned");
          $scope.$digest();
          callArgs = fakeItem.save.calls.mostRecent().args;
          expect(callArgs.length).toBe(1);
          expect(callArgs[0]).toEqual({});
        });
    });

    describe('it should add isolates', function(){
        it("should add aerobic models", function(){
          $scope.addAerobic();
          expect($scope.aerobicModels).toEqual([{aerobic: true}]);
        });

        it("should add anaerobic models", function(){
          $scope.addAnaerobic();
          expect($scope.anaerobicModels).toEqual([{aerobic: false}]);
        });
    });

    describe('it should remove isolates', function(){
        it("should remove aerobic models", function(){
          $scope.aerobicModels = [{aerobic: true}];
          $scope.deleteAerobic(0);
          expect($scope.aerobicModels).toEqual([]);
        });

        it("should remove anaerobic models", function(){
          $scope.anaerobicModels = [{aerobic: false}];
          $scope.deleteAnaerobic(0);
          expect($scope.anaerobicModels).toEqual([]);
        });
    });

    describe('is should concat the list of models to save', function(){
        it("should ignore empty models as part of the presave", function(){
          var editing = {blood_culture: {}};
          $scope.anaerobicModels = [{aerobic: false}];
          $scope.aerobicModels = [{aerobic: true}];
          $scope.preSave(editing);
          expect(editing.blood_culture.isolates).toEqual([]);
        });

        it('should concat aerobic models as part of the presave', function(){
          var editing = {blood_culture: {}};
          $scope.anaerobicModels = [{organism: 'something', aerobic: false}];
          $scope.aerobicModels = [{organism: 'something else', aerobic: true}];
          $scope.preSave(editing);
          expect(editing.blood_culture.isolates).toEqual([
            {organism: 'something else', aerobic: true},
            {organism: 'something', aerobic: false}
          ]);
        });
    });
});
