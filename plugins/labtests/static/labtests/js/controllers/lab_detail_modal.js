angular.module('opal.controllers').controller('LabDetailModalCtrl', function(
    $scope, $modalInstance, LabDetailLoader, lab_number
){
    "use strict";

    LabDetailLoader.load(lab_number).then(function(data){
        $scope.lab_data = data;
    })

    $scope.lab_number = lab_number;

    $scope.cancel = function() {
        $modalInstance.close('cancel');
    };
});
