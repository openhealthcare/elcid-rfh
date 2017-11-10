angular.module('opal.controllers').controller('ReconcilePatientCtrl',
  function($route, scope, step, episode, shortDateFilter) {
      "use strict";
      scope.demographics = angular.copy(scope.editing.demographics);
      scope.demographics.date_of_birth = shortDateFilter(scope.demographics.date_of_birth);
      var external_demographics = angular.copy(scope.editing.external_demographics);
      delete external_demographics.consistency_token;
      delete external_demographics.reconciled;
      delete external_demographics.id;
      _.extend(
        scope.editing.demographics, external_demographics
      );
      scope.editing.demographics.external_system = "RFH Demographics";
  }
);
