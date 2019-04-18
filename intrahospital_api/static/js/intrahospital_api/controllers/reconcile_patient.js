angular.module('opal.controllers').controller('ReconcilePatientCtrl',
  function(displayDateFilter, scope, step, episode) {
    "use strict";
    scope.demographics = angular.copy(scope.editing.demographics);
    scope.demographics.date_of_birth = displayDateFilter(scope.demographics.date_of_birth);

    var external_demographics = angular.copy(scope.editing.external_demographics);

    delete external_demographics.consistency_token;
    delete external_demographics.id;
    _.extend(
      scope.editing.demographics, external_demographics
    );
    scope.preSave = function(editing){
      editing.demographics.external_system = "RFH Database";
    }
  }
);
