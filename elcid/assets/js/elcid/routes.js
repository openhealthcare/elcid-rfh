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
             templateUrl: function(x){
                 // silly cache busting technique. The param is never read
                 return '/templates/covid/dashboard.html?when='+Date.now()
             },
             resolve: {
                 referencedata: function(Referencedata) { return Referencedata; },
             },
         }).when('/ICU/', {
             // This is a silly hack to let us render an arbitrary
             // template in the application viewport
             controller: 'WelcomeCtrl',
             controllerAs: 'welcome',
             templateUrl: function(x){
                 // silly cache busting technique. The param is never read
                 return '/templates/icu/dashboard.html?when='+Date.now()
             },
             resolve: {
                 referencedata: function(Referencedata) { return Referencedata; },
             },
         });
     }]);
