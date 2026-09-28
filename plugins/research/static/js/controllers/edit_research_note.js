angular.module('opal.controllers').controller('EditResearchNoteCtrl', function(
    $scope, $window, $http, $q, ngProgressLite, $modalInstance, note_text, note_id
){
    "use strict";

    var url = '/api/v0.1/researchstudynote/'+note_id+'/';

    $scope.editing = {
        'research_note': {}
    }
    $scope.editing.research_note.note = note_text;

    $scope.save = function(){
        ngProgressLite.set(0);
        ngProgressLite.start();

        $http.put(url,
                   {
                       note: $scope.editing.research_note.note
                   }
                  ).then(
            function(response){
                ngProgressLite.done();
                $window.location.reload();
            },
            function(){
                ngProgressLite.done();
                $modalInstance.close('Error');
                $window.alert('Error: Could not edit note');
            }

        );
    }

    $scope.cancel = function(){
        $modalInstance.close('Cancel');
    }

});
