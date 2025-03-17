angular.module('opal.controllers').controller(
    //
    // Helper button to remind users to record an ECG for NTM patients.
    //
    'TBOtherInvestigationsHelper',
    function($scope){
        "use strict";

        var self = this;

        self.ECG = "ECG";


        //
        // Add an investigation name and today's date
        //
        this.addECG = function(){
            $scope.name = self.ECG;
            $scope.$parent.editing.date = moment();
        }

    }
);
