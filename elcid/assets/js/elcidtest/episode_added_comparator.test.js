describe("EpisodeAddedComparator", function(){
  "use strict";
  var EpisodeAddedComparator;

  beforeEach(function(){
    module('opal.services');
    inject(function($injector){
      EpisodeAddedComparator  = $injector.get('EpisodeAddedComparator');
    });
  });

  it('it return an array of a single function', function(){
    expect(_.isArray(EpisodeAddedComparator)).toBe(true);
    expect(EpisodeAddedComparator.length).toBe(1);
    expect(_.isFunction(EpisodeAddedComparator[0])).toBe(true);
  });

  it('it return the negated episode id', function(){
    var comparatorFunc = EpisodeAddedComparator[0];
    expect(comparatorFunc({id: 10})).toBe(-10);
  });

});
