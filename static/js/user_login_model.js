UserLoginModel = function(accountLocations){
    var self = this;
    this.featuredOrganization = null;
    this.featuredSequences = [];
    self.accountLocations = accountLocations;
    self.probeinformation = []
    self.probe_with_site = new Map();
    //self.moleculeSearch = new MoleculeSearch({placeHolder: "Search for a probe"});
    self.probe_list;
    self.probe_map = new Map();
    self.all_probe_information = new Map();
    self.pure_probe_list = [];

    self.get_probe_info = function(siteName) {
        //return the list of probe information regarding the site
        return self.all_probe_information.get(siteName);
    }

    self.set_number_probelist = function(list) {
        var map = new Map();
        var result = [];
        //key = searchname, value = original list element with updated number
        for(var i = 0; i < list.length; i++) {
            if(map.has(list[i].searchName)) {
                var temp = map.get(list[i].searchName)
                temp.number = temp.number + 1
                map.delete(list[i].searchName);
                map.set(list[i].searchName, temp);
            }else{
                list[i].number = 1;
                map.set(list[i].searchName, list[i]);
            }

            if(self.probe_with_site.has(list[i].searchName)) {
                var temp = self.probe_with_site.get(list[i].searchName)
                temp.push(self.find_site_for_probe(list[i].AccountName))
                self.probe_with_site.delete(list[i].searchName)
                self.probe_with_site.set(list[i].searchName, temp)
            }else{
                temp_list = []
                account_information = self.find_site_for_probe(list[i].AccountName)
                temp_list.push(account_information)
                self.probe_with_site.set(list[i].searchName, temp_list)
            }
        }
        //make list with updated number
        for (var value of map.values()) {
            result.push(value)
        }
        // Crete site probe maping
        for(var i = 0; i < result.length; i++) {
            if(self.all_probe_information.has(result[i].AccountName)) {
                var temp = self.all_probe_information.get(result[i].AccountName)
                temp.push(result[i]);
                self.all_probe_information.delete(result[i].AccountName);
                self.all_probe_information.set(result[i].AccountName, temp);
            }else{
                temp = []
                temp.push(result[i]);
                self.all_probe_information.set(result[i].AccountName, temp)
            }
        } 

        self.probeinformation = result
        return result
    }
    self.find_site_for_probe = function(site_name) {
        for(var i = 0; i < self.accountLocations.length; i++) {
            if(site_name == self.accountLocations[i].name) {
                return self.accountLocations[i]
            }
        }
        return undefined
    } 
    self.selectLocationByProbe = function(probe) {
        newLocation = []
        newLocation = self.probe_with_site.get(probe)
        self.map.clearMarkers();
        self.map.showLocations(newLocation);
        //reset map with specific map location
        var list = self.averageGeolocation(newLocation)
        self.map.initMap(list.Latitude, list.Longitude);
        return newLocation    
    }

    /////previous////////
    self.setFeaturedOrganization = function() {
        this.featuredOrganization = null
    }
    self.set_pure_probe_list = function(list) {
        var set = new Set()
        var temp = []
        for(var i = 0;  i < list.length; i++) {
            if(!set.has(list[i].searchName)) {
               temp.push({name: list[i].Name, url: list[i].url, searchName: list[i].searchName})
                set.add(list[i].searchName)
            }
        }
        self.pure_probe_list = temp
    }

    self.set_probe_list = function() {
        $.ajax({
            type: "GET",
            url: "/account/probes/",
            success: function(res){
                    self.probe_list = res
                    self.set_pure_probe_list(self.probe_list)
                },
            error: function(err){
                    console.log(err);
                },                
        });
    }

    self.set_probe_number = function(list) {
        self.probe_map.clear()
        self.probe_counter = [];
        for(var i = 0; i < list.length; i++) {
            for(var j = 0; j < self.probe_list.length; j++) {
                if(list[i].searchName == self.probe_list[j].searchName) {
                    if(self.probe_map.has(list[i].searchName)) {
                        var temp = self.probe_map.get(list[i].searchName) + 1;
                        self.probe_map.delete(list[i].searchName);
                        self.probe_map.set(list[i].searchName, temp);
                    }else{
                        self.probe_map.set(list[i].searchName, 1);
                    }
                }
            }
        }
    }

    self.get_probe_number = function(site) {
        return self.probe_map.get(site);
    }
/*
    self.calculatedFeaturedSequences = ko.pureComputed(function(){
        $.ajax("/featured_sequences").success(function(res){
            for(var i = 0; i < res.length; i++){
                var seq = res[i];
                featuredSequences.push(new Sequence(seq));
            }
        }).fail(function(err){
            console.log(err);
        });
        return self.featuredSequences;
    });
*/
    self.initMap = function(){
        self.map = new GoogleMaps(self.locationSelected, self.accountLocations);
        self.map.showLocations(self.accountLocations);
        var list = self.averageGeolocation(self.accountLocations)
        self.map.initMap(list.Latitude, list.Longitude); 
    }

    window.matchedMolecules = function(molecules){
        var sorted = _.sortBy(molecules(), function(mole){
            var moleId = mole.record.ID();

            return typeof self.matchingMoleculeIds[moleId] !== 'undefined' ? 1 : 2;
        });
        for(var i = 0; i < sorted.length; i++) {
            if(sorted[i] != undefined) {
                if(sorted[i].Name.split("]")[1] != undefined) {
                    sorted[i].Name = sorted[i].Name.split("]")[1].replace(/(\r\n\t|\n|\r\t)/gm,"");
                }
            }
        }

        return sorted;
    }

    self.locationSelected = function(act){
        self.featuredOrganization = act;
    }

    self.locationSelectedFromResult = function(site) {
        var newLocation = []
        for(var i = 0; self.accountLocations.length; i++) {
            if(self.accountLocations[i].name == site) {
                self.map.clickSiteOnResult(self.accountLocations[i].id)
                newLocation.push(self.accountLocations[i])
                break;
            }
        } 
        self.map.clearMarkers();
        self.map.showLocations(newLocation); 
        var list = self.averageGeolocation(newLocation);
        self.map.initMap(list.Latitude, list.Longitude);
    }

    self.resetMap = function(){
        self.map.clearMarkers();
        self.map.showLocations(self.accountLocations);
        var list = self.averageGeolocation(self.accountLocations)
        self.map.initMap(list.Latitude, list.Longitude); 
    }
    self.averageGeolocation = function(coords) {
      if (coords.length === 1) {
        return coords[0];
      }

      let x = 0.0;
      let y = 0.0;
      let z = 0.0;

      for (let coord of coords) {
        let Latitude = coord.Latitude * Math.PI / 180;
        let Longitude = coord.Longitude * Math.PI / 180;

        x += Math.cos(Latitude) * Math.cos(Longitude);
        y += Math.cos(Latitude) * Math.sin(Longitude);
        z += Math.sin(Latitude);
      }

      let total = coords.length;

      x = x / total;
      y = y / total;
      z = z / total;

      let centralLongitude = Math.atan2(y, x);
      let centralSquareRoot = Math.sqrt(x * x + y * y);
      let centralLatitude = Math.atan2(z, centralSquareRoot);

      return {
        Latitude: centralLatitude * 180 / Math.PI,
        Longitude: centralLongitude * 180 / Math.PI
      };
    }



    self.contactSofie = function(){
        var title = "Contact Sofie Biosciences";
        contactUsPopup.ctrl.to_contact_name(title);
        contactUsPopup.ctrl.to_contact_url("/account/1/contact");
        contactUsPopup.open();
    }

    self.contactMatches = function(){
        var matchLen = self.map.matchesLength();
        var title = "Contact " + matchLen + " Organization" + (matchLen > 1 ? "s" : "");
        contactUsPopup.ctrl.to_contact_name(title);
        var matchingIds = self.map.matchingAccountIds().join(",");
        contactUsPopup.ctrl.to_contact_url("/account/" + matchingIds + "/contact");
        contactUsPopup.open();
    }

    self.matchingMoleculeIds = {};//new Set();
/*
    self.moleculeSearch.matches.subscribe(function(newVal){
        self.matchingMoleculeIds = {};//new Set();
        var acts = {}
        var actIds = []
        for(var i = 0; i < newVal.length; i++){
            var molecule = newVal[i];
            if(!acts[molecule.record.ID()]){
                acts[molecule.record.ID()] = true;
                actIds.push(molecule.record.ID());
                self.matchingMoleculeIds[molecule.record.ID()] = molecule;//.add(molecule.record.ID());
            }

        }
        self.moleculeSearch.isSearching(true);
        $.ajax("/account_location_molecules", {method: "post",
                                               contentType: "application/json",
                                               data: JSON.stringify({'MoleculeIDs': actIds}),
                                               headers: {}
        }).success(function(res){
            self.map.clearMarkers();
            var sofieBioInList = false;
            var sofieAccountId = 1;
            for(var i = 0; i < res.length; i++){
                var loc = res[i];
                self.map.addLocations([loc], "", loc.id);
                sofieBioInList |= loc.id == sofieAccountId;
            }

            if(sofieBioInList){
                self.map.selectAccount(sofieAccountId);
            }
            else if(res.length > 0){
                self.map.selectAccount(res[0].id);
            }

            self.moleculeSearch.isSearching(false);
        }).fail(function(err){
            self.moleculeSearch.isSearching(false);
        });
    });
    */
}