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