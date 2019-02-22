angular.module('opal.services').factory('WardComparator', function(){
    "use strict";

    var WARDS = [
        '12 North',
        '12 East',
        '12 South',
        '12 West',
        '11 North',
        '11 East',
        '11 South',
        '11 West',
        '10 North',
        '10 East',
        '10 South',
        '10 West',
        '9 North',
        '9 East',
        '9 South',
        '9 West',
        '8 North',
        '8 East',
        '8 South',
        '8 West',
        '7 North',
        '7 East',
        '7 South',
        '7 West',
        '6 North',
        '6 East',
        '6 South',
        '6 West',
        '5 North',
        '5 East',
        '5 South',
        '5 West',
        'ICU 4 East',
        'ICU 4 West',
        'ICU 4 South',
        '4 North',
        '4 East',
        '4 South',
        '4 West',
        '3 North',
        '3 East',
        '3 South',
        '3 West',
        'PITU',
        'Outpatients',
    ]

    return [
        function(p){
            var idx = WARDS.indexOf(p.location[0].ward)
            if(idx === -1){
                return WARDS.length
            }
            return idx
        },
        function(p){
            return p.id
        }
    ];
});
