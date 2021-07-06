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

var param_template_route = function(base, param_name){
    return {
        controller: 'WelcomeCtrl',
        controllerAs: 'welcome',
        templateUrl: function(params){
            return base + params[param_name] + '/?when=' + Date.now()
        },
        resolve: {
            referencedata: function(Referencedata) { return Referencedata; },
        },
    }
}

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
             .when('/list/upstream/:slug', {
                 controller: 'PatientListCtrl',
                 resolve: {
                     episodedata: function(patientListLoader, $route){
                         return patientListLoader('upstream/'+$route.current.params.slug)
                     },
                     metadata: function(Metadata){ return Metadata.load(); },
                     profile: function(UserProfile){ return UserProfile.load(); },
                 },
                 templateUrl: function(params){
                     var target =  '/templates/patient_list.html';
                     target += '/upstream/' + params.slug;
                     return target;
                 }
             })
             .when('/covid-19/',             static_template_route('/templates/covid/dashboard.html'))
             .when('/recent-covid-pos/',     static_template_route('/templates/covid/recent_positives.html'))
             .when('/covid-19/clinic-list/', static_template_route('/templates/covid/clinic_list.html'))

             .when('/ICU/',                  static_template_route('/templates/icu/dashboard.html'))
             .when('/elcid/',                static_template_route('/templates/elcid/dashboard.html'))

             .when('/lab-sync-performance/', static_template_route('/templates/monitoring/lab_timings.html'))
             .when('/system-stats/',         static_template_route('/templates/monitoring/system_stats.html'))

             .when('/tb/clinic-list/',       static_template_route('/templates/tb/clinic_list.html'))
             .when('/tb/last-30-days/',      static_template_route('/templates/tb/last_30_days.html'))
             .when('/tb/mdt-list/',          static_template_route('/templates/tb/mdt_list.html'))

             .when('/amt-covid/',            static_template_route('/templates/covid/amt_dashboard.html'))
             .when('/nursing-handover/',     static_template_route('/templates/nursing/dashboard.html'))
             .when('/beta/',                 static_template_route('/templates/elcid/beta.html'))

             .when('/admissions/transfer-history/:spell_number/',
                   param_template_route(
                       '/templates/admissions/transfer_history/', 'spell_number'))
             .when('/admissions/slice-contacts/:slice_id/',
                   param_template_route(
                       '/templates/admissions/slice_contacts/', 'slice_id'
                   ))
             .when('/admissions/location-history/:location_code',
                   param_template_route(
                       '/templates/admissions/location-history/', 'location_code'
                   ))

             .when('/ipc/',                         static_template_route('/templates/ipc/home.html'))
             .when('/ipc/wards/',                   static_template_route('/templates/ipc/wards.html'))
             .when('/ipc/ward/:ward_code/',         param_template_route('/templates/ipc/ward/', 'ward_code'))
             .when('/ipc/siderooms/',               static_template_route('/templates/ipc/siderooms.html'))
             .when('/ipc/recent-tests/:test_code/', param_template_route('/templates/ipc/recent-tests/', 'test_code'))
             .when('/ipc/alert/:alert_code/',       param_template_route('/templates/ipc/alert/', 'alert_code'))


             .when('/patient-information-load-stats/', static_template_route(
                 '/templates/monitoring/patient_information_load_stats.html'))
             .when('/imaging-load-stats/',             static_template_route(
                 '/templates/monitoring/imaging_load_stats.html'))

             .when('/nursing-handover/:ward_code/',      {
                 controller: 'WelcomeCtrl',
                 controllerAs: 'welcome',
                 templateUrl: function(params){
                     return '/templates/nursing/ward_detail.html/' + params.ward_code + '/?when=' + Date.now()
                 },
                 resolve: {
                     referencedata: function(Referencedata) { return Referencedata; },
                 },
             })
     }]);
