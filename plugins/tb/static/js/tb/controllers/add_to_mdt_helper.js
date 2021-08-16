angular.module('opal.controllers').controller('AddToMDTHelperCtrl',
  function($scope, displayDateFilter) {
    "use strict";
    var self = this;

    this.getNextDates = function(){
      var thisWednesday = null;
      _.each(_.range(7), function(d){
        var day_of_week = moment().add(d, "d").toDate();
        if(day_of_week.getDay() === 3){
          thisWednesday = day_of_week;
        }
      });
      var nextDates = [];
      _.each(_.range(4), function(i){
        nextDates.push(moment(thisWednesday).add(i * 7, "d"));
      })
      return nextDates;
    }
    this.getMDTDisplay = function(){
      var today = moment();
      var result = _.map(self.getNextDates(), function(nd){
        if(nd.isSame(today, "d")){
          return "Today";
        }
        if(moment(nd).subtract(1, "d").isSame(today, "d")){
          return "Tomorrow";
        }
        return displayDateFilter(nd);
      });
      return result;
    }
    this.getMDTValues = function(){
      var previousValue = $scope.editing.add_to_mdt.add_to_which_mdt;
      return _.map(self.getNextDates(), function(nd){
        if(previousValue){
          if(moment(previousValue).isSame(nd, "d")){
            return previousValue
          }
        }
        return nd.toDate();
      });
    }
    this.mdtDisplay = this.getMDTDisplay();
    this.mdtValues = this.getMDTValues();
    debugger;
    return this;
});
