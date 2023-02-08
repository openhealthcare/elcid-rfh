var app = angular.module('opal');

var static_template_route = function(url){
  return {
      // This is a silly hack to let us render an arbitrary
      // template in the application viewport
      controller: 'WelcomeCtrl',
      controllerAs: 'welcome',
      templateUrl: function(params){
          // silly cache busting technique. The param is never read
          params["cache_bust"] = Date.now();
          return url + '?' + $.param(params);
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
          // silly cache busting technique. The param is never read
          params["cache_bust"] = Date.now();
          return base + params[param_name] + '/?' + $.param(_.omit(params, param_name));
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
             // Although there is only one tb opal patient list route.params.slug is what is
             // used by the patient list move tag modal, so we can't hard code it.
             .when('/tb/lists/:slug/', {
                controller: 'PatientListCtrl',
                resolve: {
                    episodedata : function(patientListLoader) { return patientListLoader(); },
                    metadata   : function(Metadata){ return Metadata.load(); },
                    profile    : function(UserProfile){ return UserProfile.load(); }
                },
                templateUrl: "/templates/tb_list_tb_review_patients.html"
             })
             .when('/tb/clinic-list/',  static_template_route('/templates/tb/clinic_list/'))
             .when('/tb/clinic-list/:date_stamp',  param_template_route('/templates/tb/clinic_list/', 'date_stamp'))
             .when('/tb/last-30-days/',  static_template_route('/templates/tb/last_30_days.html'))
             .when('/tb/clinic-activity/:year/', param_template_route('/tb/clinic_activity/', 'year'))
             .when('/tb/clinic-activity/appointment_data/:year/', param_template_route('/tb/clinic_activity/appointment_data/', 'year'))
             .when('/tb/clinic-activity/mdt_data/:year/', param_template_route('/tb/clinic_activity/mdt_data/', 'year'))
             .when('/tb/mdt-outstanding/',  static_template_route('/templates/tb/outstanding_mdt_list/'))
             .when('/tb/on-tb-meds/',  static_template_route('/templates/tb/on_tb_meds/'))
             .when('/tb/mdt/:site/', param_template_route('/tb/mdt/', 'site'))

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
             .when('/admissions/bedboard/hospitals/', static_template_route('/admissions/bedboard/hospitals/'))
             .when('/admissions/bedboard/hospital/:hospital_code/',
                   param_template_route('/admissions/bedboard/hospital/', 'hospital_code'))
             .when('/admissions/bedboard/ward/:ward_name/',
                   param_template_route('/admissions/bedboard/ward/', 'ward_name'))

             .when('/ipc/',                         static_template_route('/templates/ipc/home.html'))
             .when('/ipc/bedboard/hospitals/',      static_template_route('/templates/ipc/hospitals.html'))
             .when('/ipc/bedboard/hospital/:hospital_code/',
                   param_template_route('/ipc/bedboard/hospital/', 'hospital_code'))
             .when('/ipc/bedboard/ward/:ward_name/',
                   param_template_route('/templates/ipc/ward/', 'ward_name'))

             .when('/ipc/siderooms/:hospital_code', param_template_route('/templates/ipc/isolation/', 'hospital_code'))
             .when('/ipc/alert/:alert_code/',       param_template_route('/templates/ipc/alert/', 'alert_code'))

             .when('/rnoh/inpatients/',             static_template_route('/templates/rnoh/inpatients.html'))
             .when('/rnoh/numbers/',                static_template_route('/templates/rnoh/numbers.html'))
             .when('/rnoh/ward/:ward_name/',        param_template_route('/templates/rnoh/ward_list/', 'ward_name'))

             .when('/patient-information-load-stats/', static_template_route(
                 '/templates/monitoring/patient_information_load_stats.html'))
             .when('/imaging-load-stats/',             static_template_route(
                 '/templates/monitoring/imaging_load_stats.html'))
              .when('/appointment-load-stats/', static_template_route('/templates/monitoring/appointment_load_stats.html'))
              .when('/admission-load-stats/', static_template_route('/templates/monitoring/admission_load_stats.html'))
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
             .when('/lab-test/:lab_number/',      {
                controller: "LabDetail",
                templateUrl: function(){
                    return '/templates/lab_detail.html'
                },
                resolve: {
                    lab_number: function($route){
                        return $route.current.params.lab_number;
                    },
                    lab_data: function($http, $route, LabDetailLoader) {
                        return LabDetailLoader.load($route.current.params.lab_number)
                    },
                },
            })
     }]);
