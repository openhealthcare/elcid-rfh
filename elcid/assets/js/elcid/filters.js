filters.filter('range', function(){
    return function(n) {
      var res = [];
      for (var i = 0; i < n; i++) {
        res.push(i);
      }
      return res;
    };
  });

filters.filter('month', function(){
  /*
  * A simple function that takes an integer and
  * returns the relevant month
  */
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

filters.filter('plural', function(){
  return function(someWord, count, plural){
      if(count === 1){
          return someWord;	
      }
      else if(plural){
          return plural;
      }
      return someWord + "s";	
  };
});
