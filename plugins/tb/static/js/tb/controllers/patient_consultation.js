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

        $q.all([Referencedata.load(), recordLoader.load()]).then(function(datasets){
            angular.extend($scope, datasets[0].toLookuplists());
            var item = $scope.episode.newItem("patient_consultation");

            self.editing = {patient_consultation: item.makeCopy()};
            $scope.$watch("patientConsultationForm.editing.patient_consultation", self.watchMicroFields, true);
            self.save = function(){
              ngProgressLite.set(0);
              ngProgressLite.start();
              // reset the item so that we are definitely saving
              // using the episode that is currently on scope
              var resetItem = $scope.episode.newItem("patient_consultation");
              resetItem.save(self.editing.patient_consultation).then(function() {
                  ngProgressLite.done();
                  item = $scope.episode.newItem('patient_consultation');
                  self.editing.patient_consultation = item.makeCopy();
                  self.changed = false;
              });
            };
        });
    }
 );
