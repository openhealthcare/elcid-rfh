describe('episodeVisibility', function(){
  "use strict";
  var episodeVisibility, scope, query, episode, demographics;

  beforeEach(function(){
    module('opal.services');
    inject(function($injector){
        episodeVisibility = $injector.get('episodeVisibility');
    });
    query = {hospital_number: null};

    scope = {query: query};
    demographics = {hospital_number: null, first_name: null, surname: null};
    episode = {demographics: [demographics]};
  });

  describe("it should handle empty queries", function(){
    it("should return true if the query is undefined", function(){
      query.hospital_number = null;
      expect(episodeVisibility(episode, scope)).toBe(true);
    });
    it("should return true if the query is an empty string", function(){
      query.hospital_number = "";
      expect(episodeVisibility(episode, scope)).toBe(true);
    });
  });

  describe("it should filter on hospital number, first name, surname", function(){
    it("should filter by hospital number", function(){
      demographics.hospital_number = "1231222";
      query.hospital_number = "12";
      expect(episodeVisibility(episode, scope)).toBe(true);

      demographics.hospital_number = "9888";
      query.hospital_number = "12";
      expect(episodeVisibility(episode, scope)).toBe(false);
    });

    it("should filter by first name", function(){
      demographics.first_name = "James";
      query.hospital_number = "Ja";
      expect(episodeVisibility(episode, scope)).toBe(true);

      demographics.first_name = "Sally";
      query.hospital_number = "Ja";
      expect(episodeVisibility(episode, scope)).toBe(false);
    });

    it("should filter by surname", function(){
      demographics.surname = "James";
      query.hospital_number = "Ja";
      expect(episodeVisibility(episode, scope)).toBe(true);

      demographics.surname = "Sally";
      query.hospital_number = "Ja";
      expect(episodeVisibility(episode, scope)).toBe(false);
    });
  });

  describe("it should handle case insensitivity", function(){
    it("should handle case insensitivity in the hospital number", function(){
      demographics.hospital_number = "1231222a";
      query.hospital_number = "22a";
      expect(episodeVisibility(episode, scope)).toBe(true);
    });
    it("should handle case insensitivity in the first name", function(){
      demographics.first_name = "James";
      query.hospital_number = "ja";
      expect(episodeVisibility(episode, scope)).toBe(true);
    });
    it("should handle case insensitivity in the surname", function(){
      demographics.surname = "James";
      query.hospital_number = "ja";
      expect(episodeVisibility(episode, scope)).toBe(true);
    });
  });

  describe("it should handle split strings", function(){
    it('should handle when any are present', function(){
      demographics.first_name = "Henry";
      demographics.surname = "James";
      demographics.hospital_number = "123";
      query.hospital_number = "he ja 1";
      expect(episodeVisibility(episode, scope)).toBe(true);
    });

    it('should fail if not all are present', function(){
      demographics.first_name = "Henry";
      demographics.surname = "James";
      demographics.hospital_number = "987";
      query.hospital_number = "he ja 1";
      expect(episodeVisibility(episode, scope)).toBe(false);
    });
  });
});
