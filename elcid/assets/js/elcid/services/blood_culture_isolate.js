angular.module('opal.services').service(
  'BloodCultureIsolate', function($http, $q, $window, Referencedata){
  "use strict";
  var DATE_FORMAT = 'DD/MM/YYYY'

  var baseUrl = "/elcid/v0.1/blood_culture_isolate/";

  var dateFields = ["date_positive"];

  var BloodCultureIsolate = function(blood_culture_set, item){
    if(item){
      this.isolateUrl = baseUrl + item.id + "/"
      this.isNew = false;
      this.editing = _.clone(item);
      var self = this;
      _.each(dateFields, function(dateField){
        if(self.editing[dateField]){
          self.editing[dateField] = moment(self.editing[dateField], DATE_FORMAT).toDate();
        }
      });
    }
    else{
      this.isolateUrl = baseUrl;
      this.editing = {
        consistency_token: "",
        blood_culture_set_id: blood_culture_set.id,
      }
      this.isNew = true;
    }

    // we consider an isolate and a set to be one thing
    // for the purposes of created*/updated*/previous_mrn
    // even if when we are creating a new isolate.
    this.editing.created = blood_culture_set.created;
    this.editing.created_by_id = blood_culture_set.created_by_id;
    this.editing.updated = blood_culture_set.updated;
    this.editing.updated_by_id = blood_culture_set.updated_by_id;
    this.editing.previous_mrn = blood_culture_set.previous_mrn;

    var isolate = this;

    Referencedata.load().then(function(referenceData){
      // lists should be alphabetical but with
      // Negative always as the last result
      // if the list contains negative
      var lists = [
        "gramstainoutcome_list",
        "quickfishoutcome_list",
        "gpcstaphoutcome_list",
        "gpcstrepoutcome_list"
      ]
      var lookupLists = referenceData.toLookuplists();

      _.each(lists, function(list){
        isolate[list] = lookupLists[list];
        var removed = _.without(isolate[list], 'Negative');
        if(removed.length !== isolate[list].length){
          removed.push("Negative");
          isolate[list] = removed;
        }
      });
    });
  }

  BloodCultureIsolate.prototype = {
    save: function(){
      var deferred = $q.defer();
      var method = "post";
      var self = this;
      var toSave = _.clone(this.editing);
      _.each(dateFields, function(dateField){
        if(toSave[dateField]){
          toSave[dateField] = moment(self.editing[dateField]).format(DATE_FORMAT);
        }
      });

      if(this.editing.id){
        method = "put";
      }
      $http[method](this.isolateUrl, toSave).then(
        function(){
          deferred.resolve()
        },
        function(response){
          if (response.status == 409) {
            $window.alert('Item could not be saved because somebody else has \
recently changed it - refresh the page and try again');
          } else {
              $window.alert('Item could not be saved');
          }
        }
      );

      return deferred.promise;
    },

    delete: function(){
      var deferred = $q.defer();
      $http.delete(this.isolateUrl).then(
        function() {
          deferred.resolve();
        },
        function(response) {
        // handle error better
        $window.alert('Item could not be deleted');
      });

      return deferred.promise;
    }
  }

  return BloodCultureIsolate;
});
