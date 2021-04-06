var covidDashboard = {};

covidDashboard.renderWeekGraph = function(
  elementId,
  columns,
  agesValues,
  weekLabels
) {
  /*
  * Takes in
  * elementId -> the id of an html element
  * columns -> an array of arrays that c3 takes as data, where the first item is the name of the age range
  *      e.g. [["x", 1, 2, 3],["0-35", 10, 20, 50]]
  * agesValues -> {ageRange: [absolutAgeValue]}
  *      e.g. {"0-35", [17, 23, 60}
  * weekLabels -> [weekLabelThatRelatesToAnIndex]
  *      e.g. ["4 Jan - 11 Jan"]
  */
  var colorNumbers = ["#0091C9", "#D36C08", "#a0c7ea", "#9cc96b", "#864200"];
  var colors = {};
  var ageRanges = []
  _.each(columns, function(column){
    if(column[0] !== "x"){
      ageRanges.push(column[0]);
    }
  });
  _.each(ageRanges, function (age_range, idx) {
    colors[age_range] = colorNumbers[idx];
  });

  c3.generate({
    bindto: document.getElementById(elementId),
    data: {
      x: "x",
      columns: columns,
      type: "bar",
      groups: [ageRanges],
      colors: colors,
    },
    axis: {
      x: {
        type: "category",
        tick: {
          rotate: 45,
          multiline: false,
        },
      },
      y: {
        min: 0,
        max: 100,
        padding: { top: 0, bottom: 0 },
      },
    },
    bar: {
      width: {
        ratio: 0.9,
      },
    },
    tooltip: {
      format: {
        value: function(value, ratio, id, index){
          return "" + value + "% (" + agesValues[id][index] + ")";
        },
        title: function(x){
          return "Week " + x + " (" + weekLabels[x-1] + ")";
        }
      }
    }
  });
};
