angular.module('opal.controllers').controller('RemovePatientCtrl',
  function($route, scope, step, episode) {
      "use strict";
      scope.currentTag = $route.current.params.slug;
      scope.editing.tagging[scope.currentTag] = false;
  }
);
