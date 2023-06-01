angular.module('opal.controllers').controller('IsolationHelper',
	function($scope, $http){
		var self = this;

		/*
		* this method initialises the controller
		* angular js periodically reruns template methods
		* so we wrap it in an _.once, so that its only ever
		* called once.
		*/
		this.init = _.once(function(hospital_site_code, ward_name, room, bed, isolated_bed_id){
			self.hospital_site_code = hospital_site_code;
			self.ward_name = ward_name;
			self.room = room;
			self.bed = bed;
			self.isSideRoom = room.indexOf('SR') === 0;
			if(isolated_bed_id){
				self.isolated_bed_id = isolated_bed_id
			}
			return true;
		});
		this.isolate = function(){
			var data = {
				hospital_site_code: self.hospital_site_code,
				ward_name: self.ward_name,
				room: self.room,
				bed: self.bed,
			}
			$http.post('/api/v0.1/isolated_bed/', data).then(function(response){
				self.isolated_bed_id = response.data.id;
			});
		}

		this.unisolate = function(refresh){
			$http.delete('/api/v0.1/isolated_bed/' + self.isolated_bed_id + '/').then(function(response){
			    self.isolated_bed_id = undefined;
                            if(refresh){
                                window.location.reload();
                            }
			});
		}
});
