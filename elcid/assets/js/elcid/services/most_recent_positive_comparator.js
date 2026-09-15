angular.module('opal.services').factory('MostRecentPositiveComparator', function($q, $http, $window, $log) {
    "use strict";
    // Reverse ordering by most recent postitive

    var episodeAddedComparator = function(someEpisode){
      return -someEpisode.most_recent_comparator
    };

    return [episodeAddedComparator];
});
