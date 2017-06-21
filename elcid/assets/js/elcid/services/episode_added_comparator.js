angular.module('opal.services').factory('EpisodeAddedComparator', function($q, $http, $window, $log) {
    "use strict";
    // we're ordeing by id negatively so the oldest episode is at the top

    var episodeAddedComparator = function(someEpisode){
      return -someEpisode.id
    };

    return [episodeAddedComparator];
});
