angular.module('opal.controllers').controller('RNOHAddPatientCtrl', function(scope, step, episode){
    "use strict";

    scope.preSave = function(editing){
        editing.demographics = scope.demographics;
    }

});
