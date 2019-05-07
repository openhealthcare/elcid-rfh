angular.module('opal.services').service(
  'BloodCultureIsolate', function($http, $q, $window){

  const baseUrl = "/elcid/v0.1/blood_culture_isolate/";

  class BloodCultureIsolate{
    constructor(blood_culture_set, item){
      if(item){
        this.isolateUrl = baseUrl + item.id + "/"
        this.editing = _.clone(item);
        if(item.aerobic){
          this.editing.aerobic = "Aerobic";
        }
        else{
          this.editing.aerobic = "Anaerobic";
        }
      }
      else{
        this.isolateUrl = baseUrl;
        this.editing = {
          aerobic: "Aerobic",
          consistency_token: "",
          blood_culture_set_id: blood_culture_set.id
        }
      }
    }

    save(){
      var deferred = $q.defer();
      var method = "post";
      var toSave = _.clone(this.editing);
      if(this.editing.aerobic === 'Aerobic'){
        toSave.aerobic = true;
      }
      else{
        toSave.aerobic = false;
      }

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
    }

    delete(){
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