angular.module('opal.services').service('ClinicalAdvice', function($http, $q, $window, Referencedata){
  const baseUrl = "/api/v0.1/microbiology_input/"

  class ClinicalAdvice{
    constructor(item){
      this.item = item;
      this.isNew = true;
      this.unique_id = _.uniqueId();

      // the editing object if item is not populated
      this.editing = {
        micro_input_icu_round_relation: {
          observation: {},
          icu_round: {}
        }
      };

      if(item && item.id){
        this.isNew = false;
        this.editing = item.makeCopy();
        if(item.micro_input_icu_round_relation){
          this.editing.micro_input_icu_round_relation = {
            observation: _.clone(item.micro_input_icu_round_relation.observation),
            icu_round: _.clone(item.micro_input_icu_round_relation.icu_round)
          };
        }
      }
      else{
        this.editing.when = new Date();
      }
    }

    elementName(prefix){
      /*
      because we have elements permanently in the inline
      form and in the modal unique element names
      need to be declared otherwise checkboxes
      will not work
      */
      return prefix + this.unique_id;
    }

    save(episode){
      var method;
      var self = this;
      var attrs = this.item.castToType(this.editing);
      delete attrs._client;

      if (angular.isDefined(this.item.id)) {
        method = 'put';
        url = baseUrl + attrs.id + '/';
      } else {
          method = 'post';
          attrs.episode_id = episode.id;
          url = baseUrl;
      }
      var deferred = $q.defer();

      $http[method](url, attrs).then(
        function(response) {
            self.item.initialise(response.data);
            if (method == 'post') {
              episode.addItem(self.item);
            }
            deferred.resolve();
        },
        function(response) {
            // handle error better
                if (response.status == 409) {
                    $window.alert('Item could not be saved because somebody else has \
    recently changed it - refresh the page and try again');
                } else {
                    $window.alert('Item could not be saved');
                }
                deferred.reject();
            });
        return deferred.promise
    }

    delete(){
      var deferred = $q.defer();
      var url = baseUrl + this.item.id + '/';
      var self = this;

      $http.delete(url).then(
          function(response) {
            self.item.episode.removeItem(self.item);
            deferred.resolve();
          },
            function(response) {
            // handle error better
            $window.alert('Item could not be deleted');
          });

      return deferred.promise;
    }
  }

  return ClinicalAdvice
});