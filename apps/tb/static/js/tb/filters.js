filters.filter('bmi', function(){
    "use strict";
    return function(height, weight) {
      if(height && weight){
        var bmi = weight/(height * height);
        return Math.round(bmi * 100) / 100
      }
    };
  });
