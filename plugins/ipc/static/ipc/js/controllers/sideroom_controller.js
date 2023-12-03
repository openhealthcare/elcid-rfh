angular.module('opal.controllers').controller(
    'SideroomCtrl',
    function($scope, $http, $q, SideroomLoader, profile, siderooms){

        $scope.profile  = profile;
        $scope.metadata = siderooms.metadata;
        $scope.wards    = siderooms.wards;

        // Flag to display loading gif and disable editing
        $scope.loading  = false;

        // Client side filters on room status
        $scope.bed_status_filters = 1;

        $scope.url_for_bed_patient = function(beddata){
            if(beddata.name){
                href = '/#/patient/' + beddata.patient_id;
                if(beddata.ipc_episode_id){
                    href = href + '/' + beddata. ipc_episode_id
                }
                return href
            }
            return ''
        }

        $scope.reload_beds = function(){
            //
            // We edit the sideroom status subrecord in a modal
            // This is the callback to re-render the page.
            //
            // As it can take a while we have our own loading flag
            //
            var deferred = $q.defer();

            $scope.loading = true

            SideroomLoader().then(
                function(data){
                    $scope.wards = data.wards;
                    $scope.metadata = data.metadata;

                    $scope.loading = false;
                    deferred.resolve(true)
                },
                function(data){
                    $scope.loading = false;
                    deferred.resolve(false)
                })

            return deferred.promise;
        }

        $scope.is_hidden_by_filters = function(bed){
            //
            // We have some filter buttons that restrict
            // display.
            //
            // The return this function is passed to ng-hide
            //
            if($scope.bed_status_filters == 1){
                // All
                return false
            }
            if($scope.bed_status_filters == 2){
                // Open Bays - Blue
                if(bed.is_open_bay){
                    return false
                }
                return true
            }
            if($scope.bed_status_filters == 3){
                // Main Ward - Salmon
                if(bed.is_rogue){
                    return false
                }
                return true

            }
        }



    }

)
