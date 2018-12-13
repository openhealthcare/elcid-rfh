angular.module('opal.controllers').controller(
    'ClinicalAdviceForm',
    function(
        $scope, recordLoader, ngProgressLite, $cookies,
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

        this.getClinicalAdvice = function(){
          var result = [];
          _.each($scope.patient.episodes, function(episode){
            _.each(episode.microbiology_input, function(input){
              result.push(input)
            });
          });
          this.clinicalAdvice = _.sortBy(result, "when").reverse();
        };

        this.getClinicalAdvice();

        this.editItem = function(episode, item){
          episode.recordEditor.openEditItemModal(item, 'microbiology_input').then(function(){
            self.getClinicalAdvice();
          });
        };

        $q.all([Referencedata.load(), recordLoader.load()]).then(function(datasets){
            angular.extend($scope, datasets[0].toLookuplists());
            var item = $scope.episode.newItem("microbiology_input");

            self.editing = {microbiology_input: item.makeCopy()};
            $scope.$watch("clinicalAdviceForm.editing.microbiology_input", self.watchMicroFields, true);
            self.save = function(){
              ngProgressLite.set(0);
              ngProgressLite.start();
              // reset the item so that we are definitely saving
              // using the episode that is currently on scope
              var resetItem = $scope.episode.newItem("microbiology_input");
              resetItem.save(self.editing.microbiology_input).then(function() {
                  ngProgressLite.done();
                  item = $scope.episode.newItem('microbiology_input');
                  self.editing.microbiology_input = item.makeCopy();
                  self.changed = false;
                  self.getClinicalAdvice();
              });
            };
        });
    }
 );
