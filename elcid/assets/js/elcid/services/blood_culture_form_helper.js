angular.module('opal.services').factory('BloodCultureFormHelper', function(Item){

  /*
   Blood cultures are dealt with in a staged manner
   first you perform 4 fish tests

   1. Quick Fish -> Yeast, possible results
      - Candida albicans (C. albicans)
      - Candida parapsilosis (C.parapsilosis)
      - Candida glabrata (C. glabrata)
      - Negative

    2. GPC Staph -> Gram positive cocci in clusters, possible results
      - Staphylococcus aureus (S.aureus)
      - Coagulase-negative staphylococci (CNS)
      - Negative

    3. GPC Strep -> Gram positive cocci in chains, possible results
      - Enterococcus faecalis  (E. faecalis)
      - Other enterococci
      - Negative

    3. GNR -> Gram Stain
      - E.coli
      - K. pneumoniae
      - P. aeruginosa
      - Negative
  */

  var BloodCultureFormHelper = function(bloodCulture){
      var self = this;

      if(_.isUndefined(bloodCulture.isolates)){
        bloodCulture.isolates = [];
      }
      else{
        bloodCulture.isolates = _.sortBy(bloodCulture.isolates, function(i){
          return i.aerobic;
        });
      }

      self.addAerobic = function(){
        // insert an element between the last aerobic and the
        // first anaerobic
        var firstAnaerobicIndex = _.findIndex(bloodCulture.isolates, function(bc){
          return !i.aerobic;
        });
        var isolate = {
          aerobic: true
        };
        bloodCulture.isolates.splice(firstAnaerobicIndex, 0, isolate);
      };

      self.addAnaerobic = function(){
        bloodCulture.isolates.push({
            aerobic: false,
        })
      }

      self.aerobicIsolates = function(){
        return _.filter(bloodCulture.isolates, function(bc){
            return bc.aerobic;
        });
      };

      self.anaerobicIsolates = function(){
        return _.filter(bloodCulture.isolates, function(bc){
            return !bc.aerobic;
        });
      };

      self.delete = function(index, isolate){
        if(isolate.aerobic){
            bloodCulture.isolates.splice(index, 1);
        }
        else{
            var position = self.aerobicIsolates().length + index;
            bloodCulture.isolates.splice(position, 1);
        }
      }
  };

  return BloodCultureFormHelper;
});
