angular.module('opal.controllers').controller('AddToMDTHelperCtrl',
  function($scope, displayDateFilter) {
    "use strict";
    var self = this;
    this.mdtDateStr = null;

    this.getNextDates = function(){
      /*
      * Give me the dates of the next 4 Wednesdays
      */
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
      /*
      * The next dates of the next 4 Wednesdays displayed nicely
      */
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
      /*
      * You can't save dates to radio fields
      * so we convert the dates to strings
      */
      return _.map(self.getNextDates(), function(nd){
        return nd.format('DD/MM/YYYY');
      });
    }

    var setUp = function(){
      var previous = $scope.editing.add_to_mdt.add_to_which_mdt;
      if(previous){
        self.mdtDateStr = moment(previous).format('DD/MM/YYYY');
      }
    }

    setUp();
    this.mdtDisplay = this.getMDTDisplay();
    this.mdtValues = this.getMDTValues();
    return this;
});
