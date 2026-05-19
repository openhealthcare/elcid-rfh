angular.module('opal.controllers').controller('NewResearchNoteCtrl', function(
    $scope, $window, $http, $q, ngProgressLite, $modalInstance, study_id, episode_id
){
    "use strict";

    var url = '/api/v0.1/researchstudynote/';

    $scope.save = function(){
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http.post(url,
                   {
                       episode_id: episode_id,
                       study_id  : study_id,
                       when      : $scope.editing.research_note.when,
                       note      : $scope.editing.research_note.note
                   }
                  ).then(
            function(response){
                ngProgressLite.done();
                $window.location.reload();
            },
            function(){
                ngProgressLite.done();
                $modalInstance.close('Error');
                $window.alert('Error: Could not add study');
            }

        );
    }

    $scope.cancel = function(){
        $modalInstance.close('Cancel');
    }

});
