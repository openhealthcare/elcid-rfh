angular.module('opal.controllers').controller('TBDateHelper',
    function() {
      "use strict";
      this.addMonths = function(someDt, numMonths){
        if(!someDt){
          return;
        }
        var m = moment(someDt);
        return m.add(numMonths, "months").toDate();
      }

      this.three_months_from_now = function(){
        return this.addMonths(new Date(), 3)
      }

      this.six_months_from_now = function(){
        return this.addMonths(new Date(), 6)
      }
});