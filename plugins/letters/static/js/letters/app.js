!(function() {
  var app = OPAL.module("opal.letters", [
    "ngRoute",
    "ngProgressLite",
    "ngCookies",
    "opal.config",
    "opal.filters",
    "opal.services",
    "opal.directives",
    "opal.controllers"
  ]);

  OPAL.run(app);

  app.config(function($routeProvider) {
    $routeProvider
    .when('/', {
      controller: 'PathwayRedirectCtrl',
      resolve: {},
      templateUrl: '/templates/loading_page.html'
    }).when("/:template_name*", {
      controller: "BlankCtrl",
      templateUrl: function(params) {
        return "/" + params.template_name;
      }
    });
  });
})();
