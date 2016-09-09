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
            episode: episode,
            columnName: "blood_culture"
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
          $scope.editing.blood_culture = {
            lab_number: "1"
          };
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
          expect(fakeItem.save).toHaveBeenCalledWith({lab_number: "1"});
        });
    });

    it("it should attatch form helpers", function(){
        expect(!!$scope.editing.blood_culture._formHelper).toBe(true);
    });

    it("it should remove form helpers in preSave", function(){
        $scope.preSave($scope.editing);
        expect($scope.editing.blood_culture._formHelper).toBe(undefined);
    });
});
