var map;

GoogleMaps = function(markerClickedOnEvt){
    var self = this;
    self.markers = {};
    self.mappedActs = {};
    self.markers_cluster = [];
    self.map = null;
    self.markerClickedOnEvt = markerClickedOnEvt;
    self.markerCluster;
    self.initMap = function(){
        if(arguments.length != 0) {
            var lat = arguments[0];//position.coords.latitude;
            var long = arguments[1];//position.coords.longitude;   
        }else{
            var lat = 41.14;//position.coords.latitude;
            var long = -95.97;//position.coords.longitude;   
        }
        self.map = new google.maps.Map(document.getElementById('map'), {
            center: {lat: lat, lng: long},
            scrollwheel: true,
            disableDefaultUI: true,
            zoomControl: true,
            zoom: 12,
            styles: [{"featureType":"administrative","elementType":"labels.text.fill","stylers":[{"color":"#444E58"}]},{"featureType":"landscape","elementType":"all","stylers":[{"color":"#D7D9DC"}]},{"featureType":"poi","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"poi","elementType":"labels.text","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"all","stylers":[{"saturation":-100},{"lightness":45}]},{"featureType":"road.highway","elementType":"all","stylers":[{"visibility":"simplified"}]},{"featureType":"road.arterial","elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"featureType":"transit","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"water","elementType":"all","stylers":[{"color":"#F3F6F9"},{"visibility":"on"}]}]
        });
        if(self.markers_cluster.length != 1) {
            var bounds = new google.maps.LatLngBounds();
            for (var i = 0; i < self.markers_cluster.length; i++) {
                bounds.extend(self.markers_cluster[i].getPosition());
            }
            self.map.fitBounds(bounds)        
        }
        self.markerCluster = new MarkerClusterer(self.map, self.markers_cluster,
            {imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m'});
        self.markerCluster.setGridSize(40)
    }

    self.generateHtml = function(){
        var markup =
            '<div class="map-info-wrapper" data-bind="attr:{id: \'account_\' + account.id}">' +
            '    <h3 class="h3-home-map" data-bind="text: account.name"></h3>' +
            '    <div class="map-address">' +
            '        <span data-bind="text: account.Address"></span>' +
			'        <div>' +
            '            <span class="span-map-address" data-bind="text: account.City"></span>' +
			"            <span class='span-map-address' data-bind='if: account.City && account.State'>,&nbsp;</span>"  +
            '            <span class="span-map-address" data-bind="text: account.State"></span>' +
            '            <span class="span-map-address" data-bind="text: account.ZipCode"></span>' +
			'		</div>' +
            '    </div>' +
            '    <a class="btn-gray" data-bind="click: displayPopup">Contact</a>' +
            '</div>';
        return $(markup)[0];
    }

    self.bindInfo = function(marker, siteId){
        var contentString = self.generateHtml();
        var infowindow = new google.maps.InfoWindow({
            content: contentString,
            maxWidth: 400
        });
        marker.addListener('click', function(){
            var act = self.mappedActs[siteId];
            self.closeAllAccounts();
            self.markerClickedOnEvt(act);
            //infowindow.open(self.map, marker);
        });
        var act = self.mappedActs[siteId];
        function GoogleMapsAccountInfoWindow(act, marker, infoWindow){
            var self = this;
            self.marker = marker;
            self.infoWindow = infoWindow;
            self.account = act;
            self.displayPopup = function(){
                contactUsPopup.ctrl.to_contact_name('Contact ' + self.account.name);
                contactUsPopup.ctrl.to_contact_url("/account/" + self.account.id + "/contact");
                contactUsPopup.open();
            }
        }
        var markerCtrl = new GoogleMapsAccountInfoWindow(act, marker, infowindow);
        self.markers[siteId] = markerCtrl;
        ko.applyBindings(markerCtrl, infowindow.content);
    }

    self.clickSiteOnResult = function(site_number) {
        self.markerClickedOnEvt(self.mappedActs[site_number]);
    }

    self.showLocations = function(locations){
        self.markers_cluster = []
        for(var i = 0; i < locations.length; i++){
            var site = locations[i];
            self.mappedActs[site.id] = new Account(site);
            self.addLocations([site],site.name, site.id);
        }
    }

    self.addLocations = function(locations, title, account_id){
        for(var j = 0; j < locations.length; j++){
            var location =locations[j];
            if(location.Latitude != null && location.Longitude != null){
                var myLatLng = {lat: location.Latitude, lng: location.Longitude};
                var name = title;
                if(location.Pharma) {
                    var marker = new google.maps.Marker({
                        position: myLatLng,
                        map: self.map,
                        title: name,
                        icon: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
                    });
                }else{
                    var marker = new google.maps.Marker({
                        position: myLatLng,
                        map: self.map,
                        title: name,
                        icon: 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png'
                    }); 
                }

                self.bindInfo(marker, account_id);
                self.markers_cluster.push(marker)
            }
        }   
        if(account_id == 1){
            //self.selectAccount(account_id);
        }
    }

    self.matchesLength = function(){
        var count = 0;
        for(var key in self.markers){
            count++;
        }
        return count;
    }

    self.matchingAccountIds = function(){
        var keys = [];
        for(var key in self.markers){
            keys.push(key);
        }
        return keys;
    }

    self.selectAccount = function(actId){
        var selectedCtrl = self.markers[actId];

        if(selectedCtrl){
            self.markerClickedOnEvt(self.mappedActs[actId]);
            selectedCtrl.infoWindow.open(self.map, selectedCtrl.marker);
        }
    }

    self.closeAllAccounts = function(){
        for(var key in self.markers){
            var marker = self.markers[key];
            marker.infoWindow.close();
        }
    }

    self.clearMarkers = function(){
        for(var key in self.markers){
            var marker = self.markers[key];
            marker.marker.setMap(null);
        }
        self.markers = {};
    }

}