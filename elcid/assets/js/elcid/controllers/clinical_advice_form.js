angular.module('opal.controllers').controller(
    'ClinicalAdviceForm',
    function(
        $rootScope, $scope, $window, recordLoader, ngProgressLite, $cookies,
        Referencedata, $q
      ){
        "use strict";

        var self = this;

        $q.all([Referencedata, recordLoader]).then(function(datasets){

            angular.extend($scope, datasets[0].toLookuplists());
            var item = $scope.episode.newItem("microbiology_input", {column: $rootScope.fields.microbiology_input});
            self.editing = item.makeCopy();

            self.save = function(){
              ngProgressLite.set(0);
              ngProgressLite.start();
              item.save(self.editing).then(function() {
                  ngProgressLite.done();
                  item = $scope.episode.newItem('microbiology_input', {column: $rootScope.fields.microbiology_input});
                  self.editing = item.makeCopy();
              });
            };
        });
    }
 );
