angular.module('opal.controllers').controller('NewSubrecordStepCtrl',
  function(step, scope, episode, recordLoader, $window) {
      "use strict";
      var oldData = [];
      if(scope.editing[step.model_api_name]){
        if(_.isArray(scope.editing[step.model_api_name])){
          oldData = scope.editing[step.model_api_name]
        }
        else{
          oldData = [scope.editing[step.model_api_name]]
        }
      }
      scope.editing[step.model_api_name] = {}

      scope.preSave = function(editing){
        oldData.push(scope.editing[step.model_api_name])
        editing[scope.editing[step.model_api_name]] = oldData;
      }

});
