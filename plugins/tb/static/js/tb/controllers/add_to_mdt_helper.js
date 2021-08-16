angular.module('opal.controllers').controller('AddToMDTHelperCtrl',
  function($scope, displayDateFilter) {
    "use strict";
    var self = this;
    this.nextDates = function(){
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
    this.mdt_display = function(){
      var today = moment();
      var result = _.map(self.nextDates(), function(nd){
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
    this.mdt_values = function(){
      return _.map(self.nextDates(), function(nd){
        return nd.format('DD/MM/YYYY');
      });
    }
    return this;
});
