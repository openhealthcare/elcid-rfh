angular.module('opal.controllers').controller(
    'ClinicalAdviceForm',
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

        $q.all([Referencedata, recordLoader]).then(function(datasets){
            angular.extend($scope, datasets[0].toLookuplists());
            var item = $scope.episode.newItem("microbiology_input", {column: $rootScope.fields.microbiology_input});

            self.editing = {microbiology_input: item.makeCopy()};
            $scope.$watch("clinicalAdviceForm.editing.microbiology_input", self.watchMicroFields, true);
            self.save = function(){
              ngProgressLite.set(0);
              ngProgressLite.start();
              item.save(self.editing.microbiology_input).then(function() {
                  ngProgressLite.done();
                  item = $scope.episode.newItem('microbiology_input', {column: $rootScope.fields.microbiology_input});
                  self.editing.microbiology_input = item.makeCopy();
                  self.changed = false;
              });
            };
        });
    }
 );
