describe("BloodCultureFormHelper", function(){
  "use strict";
  var BloodCultureFormHelper;
  var bloodCultureFormHelper;
  var bloodCultureRecord;
  var aerobic, anaerobic;

  var loadInIsolates= function(bcr){
    aerobic = [{
      aerobic: true,
      consistency_token: "1"
    }, {
      aerobic: true,
      consistency_token: "2"
    }];

    anaerobic = {
      aerobic: false,
      consistency_token: "3"
    }

    _.each(aerobic, function(x){
      bcr.isolates.push(x);
    });

    bcr.isolates.push(anaerobic);
  }

  beforeEach(function(){
    module('opal');
    inject(function($injector){
      BloodCultureFormHelper = $injector.get('BloodCultureFormHelper');
    });
    bloodCultureRecord = {};
    bloodCultureFormHelper = new BloodCultureFormHelper(bloodCultureRecord);
  });

  it("should sort blood cultures on load", function(){
    var tests = [{
      aerobic: true,
      consistency_token: "1"
    }, {
      aerobic: false,
      consistency_token: "2"
    }, {
      aerobic: true,
      consistency_token: "3"
    }];

    var bc = {isolates: tests};

    BloodCultureFormHelper(bc);

    var tokens = _.pluck(bc.isolates, "consistency_token");
    expect(tokens).toEqual(["2", "1", "3"]);
  });

  it("should add aerobic bloodcultures", function(){
      bloodCultureFormHelper.addAerobic();
      expect(bloodCultureRecord.isolates[0].aerobic).toBe(true);
  });

  it("should add anaerobic bloodcultures", function(){
      bloodCultureFormHelper.addAnaerobic();
      expect(bloodCultureRecord.isolates[0].aerobic).toBe(false);
  });

  it("should show only filter anaerobic isolates", function(){
    loadInIsolates(bloodCultureRecord);
    var anaerobicIsolates = bloodCultureFormHelper.anaerobicIsolates();
    expect(anaerobicIsolates).toEqual([anaerobic]);
  });

  it("should show only filter aerobic isolates", function(){
    loadInIsolates(bloodCultureRecord);
    var aerobicIsolates = bloodCultureFormHelper.aerobicIsolates();
    expect(aerobicIsolates).toEqual(aerobic);
  });

  it("it should remove aerobic", function(){
    loadInIsolates(bloodCultureRecord);
    bloodCultureFormHelper.delete(1, aerobic[1]);
    expect(bloodCultureRecord.isolates).toEqual([
      aerobic[0], anaerobic
    ]);
  });

  it("it should remove anaerobic", function(){
    loadInIsolates(bloodCultureRecord);
    bloodCultureFormHelper.delete(0, anaerobic);
    expect(bloodCultureRecord.isolates).toEqual(aerobic);
  });


});
