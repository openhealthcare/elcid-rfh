angular.module('opal.services')
    .factory('episodeVisibility', function(){
      "use strict";

    /*
    * An override that allows us to query by hospital number, first_name
    * surname.
    *
    * We overload the query.hospital_number field and just filter
    * everything based on this
    *
    * we split with a space so if you do 21 Ja, you get anyone
    * whose hospital number, first name or surnbame containes 21
    * and
    * whose hospital number, first name or surnbame containes ja
    *
    * every element of the query string needs to appear in
    * at least one of first_name, surname, hospital_number regardless of case
    */
    return function(episode, $scope) {
        var query = $scope.query.hospital_number;
        if(query && query.length){
          var demographics = episode.demographics[0];
          var first_name = demographics.first_name;
          var surname = demographics.surname;
          var hospital_number = demographics.hospital_number;
          var querySplit = _.map(query.split(" "), function(q){return q.toLowerCase(); });
          return _.every(querySplit, function(qs){
            return _.any([first_name, surname, hospital_number], function(param){
              if(param){
                return param.toLowerCase().indexOf(qs) !== -1;
              }
              else{
                return false;
              }
            });
          });
        }
        else{
          return true;
        }
    };
});
