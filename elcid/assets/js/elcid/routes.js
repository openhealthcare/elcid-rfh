var app = angular.module('opal');
app.config(
    ['$routeProvider',
     function($routeProvider){
	     $routeProvider.when('/',  {
            controller: 'WelcomeCtrl',
            controllerAs: 'welcome',
            templateUrl: '/templates/welcome.html',
            resolve: {
              referencedata: function(Referencedata) { return Referencedata; },
            },
        });
     }]);
