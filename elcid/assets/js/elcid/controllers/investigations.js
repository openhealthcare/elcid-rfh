controllers.controller('InvestigationsCtrl',
    function($scope, $http) {
      "use strict";
      var self = this;
      $http.get("/glossapi/v0.1/relevent_lab_test_api/").then(function(result){
        self.data = result.data;
        var data = ['values']
        _.each(self.data[0].values, function(someData){
          data.push(parseInt(someData[0]));
        });

        _.each(self.data, function(data){
          data.graphValues = _.map(self.data[0].values, function(someData){
            return parseInt(someData[0]);
          });
        });
      });
});
