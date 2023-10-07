angular.module('opal.controllers').controller(
    'ElcidPostLoginCtrl',
    function($scope, $location, profile) {
        if(_.contains(profile.active_roles(), 'ipc_portal_only')){
            $location.path('/ipc/portal/')
            return
        }
        return
    }
);
