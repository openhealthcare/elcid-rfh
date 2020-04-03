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
         }).when('/covid-19/', {
             // This is a silly hack to let us render an arbitrary
             // template in the application viewport
             controller: 'WelcomeCtrl',
             controllerAs: 'welcome',
             templateUrl: '/templates/covid/dashboard.html',
             resolve: {
                 referencedata: function(Referencedata) { return Referencedata; },
             },
         });
     }]);
