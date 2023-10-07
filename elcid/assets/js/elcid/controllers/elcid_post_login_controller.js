angular.module('opal.controllers').controller(
    'ElcidPostLoginCtrl',
    function($scope, $location, profile) {
        if(_.contains(profile.active_roles(), 'ipc_portal_only')){
            $location.path('/ipc/portal/')
            return
        }
        if(_.contains(profile.active_roles(), 'bed_manager')){
            $location.path('/ipc/')
            return
        }
        return
    }
);
