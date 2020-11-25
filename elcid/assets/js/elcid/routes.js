var app = angular.module('opal');

var static_template_route = function(url){
  return {
      // This is a silly hack to let us render an arbitrary
      // template in the application viewport
      controller: 'WelcomeCtrl',
      controllerAs: 'welcome',
      templateUrl: function(x){
          // silly cache busting technique. The param is never read
          return url + '?when=' + Date.now()
      },
      resolve: {
          referencedata: function(Referencedata) { return Referencedata; },
      },
  }

};

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
         })
             .when('/covid-19/',             static_template_route('/templates/covid/dashboard.html'))
             .when('/ICU/',                  static_template_route('/templates/icu/dashboard.html'))
             .when('/elcid/',                static_template_route('/templates/elcid/dashboard.html'))
             .when('/lab-sync-performance/', static_template_route('/templates/monitoring/lab_timings.html'))
             .when('/amt-covid/',            static_template_route('/templates/covid/amt_dashboard.html'))

     }]);
