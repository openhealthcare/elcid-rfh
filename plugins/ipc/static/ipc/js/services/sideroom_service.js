angular.module('opal.services').factory('SideroomLoader', function(
    $q, $http, $route, $window
){
    return function(){
        "use strict";

        var deferred = $q.defer();
        var hospital_code = $route.current.params.hospital_code;

        var target = 'api/v0.1/sideroomlist/' + hospital_code + '/';

        $http.get(target).then(
            function(response){
                deferred.resolve(response.data)
            },
            function(){
                $window.alert('Sideroom data could not be loaded');
            })

        return deferred.promise;
    }
})
