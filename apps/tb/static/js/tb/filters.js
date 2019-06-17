filters.filter('bmi', function(){
  "use strict";
  return function(height, weight) {
    if(height && weight){
      var bmi = weight/(height * height);
      return Math.round(bmi * 100) / 100
    }
  };
});

filters.filter('markdown', function () {
  return function(input){
    if(!input){
      return "";
    }
    var renderMarkdown = function(unrendered){
      var converter = new Showdown.converter({extensions: [OpalDown]});
      return converter.makeHtml(unrendered);
    }
    return renderMarkdown(input)
  }
});

filters.filter('month', function(){
  return function(input){
    if(input == 1){
      return "Jan";
    }
    if(input == 2){
      return "Feb";
    }
    if(input == 3){
      return "Mar";
    }
    if(input == 4){
      return "Apr";
    }
    if(input == 5){
      return "May";
    }
    if(input == 6){
      return "Jun";
    }
    if(input == 7){
      return "Jul";
    }
    if(input == 8){
      return "Aug";
    }
    if(input == 9){
      return "Sep";
    }
    if(input == 10){
      return "Oct";
    }
    if(input == 11){
      return "Nov";
    }
    if(input == 12){
      return "Dec";
    }
    return "";
  }
});
