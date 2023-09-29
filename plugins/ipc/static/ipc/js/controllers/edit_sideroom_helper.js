angular.module(
    'opal.controllers').controller(
        'EditSideroomHelper',
	function($scope, $http, patientLoader){
	    var self = this;

            this.edit_status = function(patient_id){
                patientLoader(patient_id).then(function(patient){
                    patient.recordEditor.editItem(
                        'sideroom_status', patient.sideroom_status[0]
                    ).then(
                        function(status){
                            if(status === "cancel"){
                                return
                            }
                            window.location.reload();
                        }
                    );
                })
            }
        });
