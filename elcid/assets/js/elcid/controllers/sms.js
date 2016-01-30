angular.module('opal.controllers')
    .controller('SMSCtrl',
                function ($scope, $modalInstance, episode) {

                    $scope.episode = episode;
                    console.log($scope.episode)
                    $scope.editing = {message: null}
                    $scope.templates = {
                        'bloods_due': function(){
                            if($scope.episode){
                                date = moment($scope.episode.ibd_info[0].next_blood).format("ddd, MMM hA")
                            }else{
                                date = '$date';
                            }

                            msg = 'Reminder: Your Bloods are due on ' + date + ' If you need blood forms please ring 02090 7120 643 '
                            return msg
                        }
                    }

                    $scope.template = function(what){
                        $scope.editing.message = $scope.templates[what]()
                    }

                    $scope.cancel = function () {
                        $modalInstance.dismiss('cancel');
                    };
                });
