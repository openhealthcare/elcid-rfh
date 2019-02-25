describe("WardComparator", function(){
    "use strict";
    var WardComparator;

    beforeEach(function(){
        module('opal.services');
        inject(function($injector){
          WardComparator  = $injector.get('WardComparator');
        });
    });

    it("should work with a ward", function(){
        var episode = {
            location: [{
                ward: "12 North"
            }]
        }
        expect(WardComparator[0](episode)).toBe(0);
    });

    it("should work with ward in the correct order", function(){
        var episode1 = {
            location: [{
                ward: "12 North"
            }]
        }
        var episode2 = {
            location: [{
                ward: "12 South"
            }]
        }
        var episode3 = {
            location: [{
                ward: "11 North"
            }]
        }
        expect(WardComparator[0](episode1)).toBe(0);
        expect(WardComparator[0](episode2)).toBe(2);
        expect(WardComparator[0](episode3)).toBe(4);
    });

    it("should work with an unknown ward", function(){
        var episode = {
            location: [{
                ward: "unknown ward"
            }]
        }
        expect(WardComparator[0](episode)).toBe(45);
    });

    it("should work with an empty string", function(){
        var episode = {
            location: [{
                ward: ""
            }]
        }
        expect(WardComparator[0](episode)).toBe(45);
    });

    it("should work with episode id order", function(){
        var episode = {id: 1}
        expect(WardComparator[1](episode)).toBe(1);
    });
});