module.exports = function(config){
  var opalPath = process.env.OPAL_LOCATION;
  var karmaDefaults = require(opalPath + '/opal/tests/js_config/karma_defaults.js');
  var baseDir = __dirname + '/..';
  var coverageFiles = [
    __dirname + '/../elcid/assets/js/elcid/*',
    __dirname + '/../elcid/assets/js/elcid/controllers/*',
    __dirname + '/../elcid/assets/js/elcid/services/*',
    __dirname + '/../elcid/assets/js/elcid/services/records/*',
    __dirname + '/../intrahospital_api/static/js/intrahospital_api/controllers/*',
    __dirname + '/../apps/tb/static/js/tb/controllers/*',
  ];
  var includedFiles = [
    'opal/app.js',
    __dirname + '/../elcid/assets/js/elcid/**/*.js',
    __dirname + '/../elcid/assets/js/elcidtest/*.js',
    __dirname + '/../intrahospital_api/static/js/intrahospital_api/*.js',
    __dirname + '/../apps/tb/static/js/tb/controllers/*',
    __dirname + '/../apps/tb/static/js/test/**/*',
  ];

  var defaultConfig = karmaDefaults(includedFiles, baseDir, coverageFiles);
  config.set(defaultConfig);
};
