angular.module('opal.services').factory('$exceptionHandler', function($injector, $log) {
    "use strict";
    var errorCatcherHandler = function errorCatcherHandler(exception, cause) {
        // we use the injector to stop a circular dependency as per
        // https://stackoverflow.com/questions/22332130/injecting-http-into-angular-factoryexceptionhandler-results-in-a-circular-de
        var $http = $injector.get("$http");
        var url = "/elcid/v0.1/error_emailer/"
        $http.post(url, {exception: exception, cause: cause});
        $log.error(exception);
    };

    return errorCatcherHandler;
})
