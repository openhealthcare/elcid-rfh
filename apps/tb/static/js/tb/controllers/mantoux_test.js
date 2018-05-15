angular.module('opal.controllers').controller('MantouxTestCrtl',
  function(step, scope, episode, recordLoader, $window) {
    "use strict";

    if(scope.editing.mantoux_test.length){
      var mantoux_tests = _.map(scope.editing.mantoux_test, function(x){
        return {mantoux_test: x}
      });
      scope.mantoux_tests = _.sortBy(mantoux_tests, function(x){
        return x.mantoux_test.site;
      });
    }
    else{
      scope.mantoux_tests = [
        {
          mantoux_test: {
            site: "Left Lower Arm",
            _client: {id: _.uniqueId("mantoux_test") }
          }
        },
        {
          mantoux_test: {
            site: "Left Lower Arm",
            _client: {id: _.uniqueId("mantoux_test") }
          }
        }
      ]
    }

    scope.preSave = function(editing){
      editing.mantoux_test = [
        scope.mantoux_tests[0].mantoux_test,
        scope.mantoux_tests[1].mantoux_test,
      ]
    }
});
