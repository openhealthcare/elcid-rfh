controllers.controller('AsyncLoad', function($scope, $http, $window){
  "use strict";
  this.states = {
    LOADING: "LOADING",
    RESOLVED: "RESOLVED",
  }
  this.state = null;
  this.taskId = null;
  var self = this;

  this.load = function(url){
    self.state = self.states.LOADING;
    self.taskId = null;
    $http.get(url).then(
      function(result){
        self.taskId = result.data.id;
        self.state = self.states.RESOLVED;
      },
      function(){
        $window.alert('Item could not be saved');
      }
    )
  }
});