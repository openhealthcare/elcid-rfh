angular.module('opal.controllers').controller(
    'PatientConsultationForm',
    function(
        $rootScope, $scope, $window, recordLoader, ngProgressLite, $cookies,
        Referencedata, $q
      ){
        "use strict";

        var self = this;
        this.changed = false;

        this.watchMicroFields = function(mi){
          // apart from the keys when, _client, initials, are any of the fields not falsy, ie undeinfed
          self.changed = !!_.compact(_.filter(mi, function(val, key){
            return !(key == 'when' || key == '_client' || key == "initials");
          })).length;
        };

        this.getEditing = function(){
          // The patient consultation service uses the users initials.
          //
          // The users initials are first_name + " " + surname
          // i.e. if there is no first name or surname initals is set
          // to " "
          //
          // so strip the initials to make sure they are empty if not
          // populated and this means that the required will work
          // on the template tag.
          var item = $scope.episode.newItem("patient_consultation");
          var editing = {patient_consultation: item.makeCopy()};
          if(editing.patient_consultation.initials){
            editing.patient_consultation.initials = editing.patient_consultation.initials.trim();
          }
          return editing;
        }

        $q.all([Referencedata.load(), recordLoader.load()]).then(function(datasets){
            angular.extend($scope, datasets[0].toLookuplists());
            var item = $scope.episode.newItem("patient_consultation");
            self.editing = self.getEditing();
            $scope.$watch("patientConsultationForm.editing.patient_consultation", self.watchMicroFields, true);
            self.save = function(form){
              ngProgressLite.set(0);
              ngProgressLite.start();
              // reset the item so that we are definitely saving
              // using the episode that is currently on scope
              var resetItem = $scope.episode.newItem("patient_consultation");
              resetItem.save(self.editing.patient_consultation).then(function() {
                  ngProgressLite.done();
                  item = $scope.episode.newItem('patient_consultation');
                  self.editing = self.getEditing();
                  self.changed = false;
                  form.$setPristine()
              });
            };
        });
    }
 );
