describe('AddEpisodeHelperCtrl', function(){
    "use strict";
    var $rootScope, ngProgressLite, $location, $controller;
    var  $httpBackend, FieldTranslator, controller, $scope;
    var opalTestHelper;

    beforeEach(function(){
        module('opal.controllers');
        module('opal.test');
        inject(function($injector){
            $rootScope   = $injector.get('$rootScope');
            $controller  = $injector.get('$controller');
            $location  = $injector.get('$location');
            ngProgressLite  = $injector.get('ngProgressLite');
            $httpBackend  = $injector.get('$httpBackend');
            FieldTranslator = $injector.get('FieldTranslator');
            $scope = $rootScope.$new();
            opalTestHelper = $injector.get('opalTestHelper');
        });

        controller = $controller('AddEpisodeHelperCtrl', {
            FieldTranslator: FieldTranslator,
            $scope: $scope,
            $location: $location,
            ngProgressLite: ngProgressLite
        });
        $scope.patient = opalTestHelper.newPatient($rootScope);
    });

    describe("addEpisode", function(){
        beforeEach(function(){
            var expectedPost =  {
                "demographics":{
                    "id": 101,
                    "first_name": "John",
                    "surname": "Smith",
                    "date_of_birth": "31/07/1980",
                    "created": "07/04/2015 11:45:00"
                },
                "category_name": "TB",
                "start": moment().format('DD/MM/YYYY')
            }
            $httpBackend.expectPOST('/api/v0.1/episode/', expectedPost).respond({
                id: 3
            });
            spyOn(ngProgressLite, "set");
            spyOn(ngProgressLite, "start");
            spyOn(ngProgressLite, "done");
            spyOn($location, "path");
        });

        afterEach(function(){
            $httpBackend.verifyNoOutstandingExpectation();
            $httpBackend.verifyNoOutstandingRequest();
        });

        it("should create an episode", function(){
            controller.addEpisode("TB");
            expect(ngProgressLite.set).toHaveBeenCalledWith(0);
            expect(ngProgressLite.start).toHaveBeenCalledWith();
            $httpBackend.flush();
            expect(ngProgressLite.done).toHaveBeenCalledWith();
            expect($location.path).toHaveBeenCalledWith('/patient/1/3');
        });
    });

    describe("hasEpisodeCategory", function(){
        it("should return true when episode category is found", function(){
            $scope.patient.episodes = [{category_name: "TB"}];
            expect(controller.hasEpisodeCategory("TB")).toBe(true);
        });

        it("should return false when episode category is now found", function(){
            $scope.patient.episodes = [{category_name: "TB"}]
            console.error(controller);
            expect(controller.hasEpisodeCategory("else")).toBe(false);
        });
    })
});