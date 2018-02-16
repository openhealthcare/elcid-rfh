angular.module('opal.controllers').controller('TbSymptomComplexCrtl',
  function(step, scope, episode, recordLoader, $window) {

    if(_.isArray(scope.editing.symptom_complex)){
      if(!scope.editing.symptom_complex.length){
        scope.editing.symptom_complex = {}
      }
      else{
        scope.editing.symptom_complex = _.first(scope.editing.symptom_complex);
      }
    }

    if(!scope.editing.symptom_complex){
      scope.editing.symptom_complex = {};
    }

     if(!scope.editing.symptom_complex.symptoms){
       scope.editing.symptom_complex.symptoms = [];
     }
     tBSymptoms = [
       "Cough (Dry)",
       "Cough (Productive)",
       "Coughing up blood",
       "Breathlessness",
       "Fatigue",
       "Fever",
       "Loss of Appetite",
       "Night Sweats",
       "Swelling in the lymph node",
       "Weight Loss"
     ]

    scope.tbSymptomFields = {};
    _.map(tBSymptoms, function(tBSymptom){
      scope.tbSymptomFields[tBSymptom] = tBSymptom;
    });

    scope.tbSymptom = {};

    var tbValues = _.keys(scope.tbSymptomFields);

    // we add plus 1 to round down
    // so if for example we had 3 items
    // the first item would have 2 in it and the
    // the second 1, rather than the othe way round
    column1 = tbValues.slice(0, (tbValues.length + 1)/2);
    column2 = tbValues.slice((tbValues.length + 1)/2);
    scope.columns = [column1, column2];

    scope.updateTbSymptoms = function(){
      var symptoms = scope.editing.symptom_complex.symptoms;

      var relevent = _.intersection(_.values(scope.tbSymptomFields), symptoms);

      _.each(scope.tbSymptomFields, function(v, k){
        var toAdd = _.contains(relevent, v);

        if(scope.tbSymptom[k]){
          scope.tbSymptom[k] = toAdd;
        }
        else if(!scope.tbSymptom[k] && toAdd){
          scope.tbSymptom[k] = toAdd;
        }
      });
    };

    scope.updateTbSymptoms();

    scope.updateSymptoms = function(symptomField){
      var symptoms = scope.editing.symptom_complex.symptoms || [];

      var symptomValue = scope.tbSymptomFields[symptomField]
      var inSymptoms = _.find(symptoms, function(x){
         return x === symptomValue;
      });
      var toAdd = scope.tbSymptom[symptomField];

      if(!inSymptoms && toAdd){
        symptoms.push(symptomValue);
      }
      else if(inSymptoms && !toAdd){
        symptoms = _.filter(symptoms, function(x){
            return x !== symptomValue;
        });

        scope.editing.symptom_complex.symptoms = symptoms;
      }
    };

    scope.preSave = function(editing){
      if(!editing.symptom_complex.symptoms.length){
         delete editing.symptom_complex;
      }
    }
});
