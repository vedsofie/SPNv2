function Account(details){
    var self = this;
    details = details || {};
    $.extend(self, details);
    self.initRecord = function(){
        self.record = new Record(self);

        var canEditName = true;
        var isAdmin = true;
        if(typeof runningUser !== 'undefined'){
            canEditName = runningUser.RoleType == 'super-admin';
            isAdmin = runningUser.RoleType == 'super-admin';
        }

        self.record.addColumn("id", true, {isNumber: true});
        self.record.addColumn("name", canEditName, {presence: true, length:{maximum: 42}});
        self.record.addColumn("description", true, {length: {maximum: 500}});
        self.record.addColumn("image");
        self.record.addColumn("primary_contact_id", true, {isNumber: true});
        self.record.addColumn("City", true, {length: {maximum: 100}});
        self.record.addColumn("State", true, {length: {maximum: 100}});
        self.record.addColumn("ZipCode", true, {length: {maximum: 20}});
        self.record.addColumn("Address", true, {length: {maximum: 100}});
        self.record.addColumn("Latitude", isAdmin, {isNumber: true});
        self.record.addColumn("Longitude", isAdmin, {isNumber: true});
        self.record.addColumn("LabName", true, {length: {maximum: 100}});
        self.record.addColumn("PrincipalInvestigatorID", true, {isNumber: true});
    }
    self.searchingCoords = ko.observable(false);
    self.initRecord(self);

    self.revert = function(){
        self.record = null;
        self.initRecord(self);
    }

    self.allSequences = ko.observableArray();
    self.sequences = ko.observableArray();
    self.users = ko.observableArray();
    var seq_count = details.sequence_count === 'undefined' ? null : details.sequence_count
    self.sequence_count = ko.observable(seq_count);
    self.user_count = ko.observable("x");
    self.principal_investigator = ko.observable();
    self.primary_contact = ko.observable(self.primary_contact_id ? self.primary_contact_id : null);
    self.canSave = ko.observable(false);

    self.toggleEditMode = function(){
        self.canSave(!self.canSave());
    }

    self.details_url = function(){
        return "/account/" + self.id;
    }

    self.calculated_sequence_count = ko.pureComputed(function(){
        if(self.id && self.sequence_count() == null){
            $.ajax("/account/" + self.id + "/sequence_count", {
                cache: false,
                headers: {"Accept": "application/json"},
                success: function(res){
                    res = JSON.parse(res);
                    self.sequence_count(res);
                }
            });
        }
        return self.sequence_count;
    });
	
	self.hasSequences = ko.pureComputed(function(){
		return self.sequences().length > 0;
	});

    self.calculated_user_count = ko.pureComputed(function(){
        if(self.id){
            $.ajax("/account/" + self.id + "/user_count", {
                cache: false,
                headers: {"Accept": "application/json"},
                success: function(res){
                    res = JSON.parse(res);
                    self.user_count(res);
                }
            });
        }
        return self.user_count;
    });
    var sequencesNeedCalculation = true;

    self.calculatedSequences = ko.pureComputed(function(){
        if(self.allSequences().length == 0 && sequencesNeedCalculation){
            sequencesNeedCalculation = false;
            $.ajax("/account/" + self.id + "/sequences", {
                cache: false,
                headers: {"Accept": "application/json"},
                success: function(res){
                    var seqs = initSequences(JSON.parse(res));
                    self.sequences(seqs);
                    self.allSequences(seqs);
                }
            });
        }
        return self.sequences;
    });
    self.paginationSize = 3;
    self.publicSequences = ko.observableArray();
    self.publicSequencePage = ko.observable(1);
    self.privateElixysSequences = ko.observableArray();
    self.privateElixysSequencePage = ko.observable(1);
    self.privateSequences = ko.observableArray();
    self.privateSequencePage = ko.observable(1);
    self.calculatedPublicSequences = ko.pureComputed(function(){
        self.publicSequences([]);
        self.calculatedSequences();
        for(var i = 0; i < self.sequences().length; i++){
            var sequence = self.sequences()[i];
            if(sequence.MadeOnElixys && sequence.IsDownloadable){
                self.publicSequences.push(sequence);
            }
        }
        return self.publicSequences;
    });

    self.calculatedPrivateElixysSequences = ko.pureComputed(function(){
        self.privateElixysSequences([]);
        self.calculatedSequences();
        for(var i = 0; i < self.sequences().length; i++){
            var sequence = self.sequences()[i];
            if(!sequence.IsDownloadable && sequence.MadeOnElixys){
                self.privateElixysSequences.push(sequence);
            }
        }
        return self.privateElixysSequences;
    });

    self.calculatedPrivateSequences = ko.pureComputed(function(){
        self.privateSequences([]);
        self.calculatedSequences();
        for(var i = 0; i < self.sequences().length; i++){
            var sequence = self.sequences()[i];
            if(!(sequence.IsDownloadable || sequence.MadeOnElixys)){
                self.privateSequences.push(sequence);
            }
        }
        return self.privateSequences;
    });

    self.probes = ko.observableArray();
    self.calculatedUniqueMolecules = ko.pureComputed(function(){
        $.ajax("/account/" + self.id + "/probes", {
            cache: false,
            headers: {"Accept": "application/json"},
            success: function(res){
                var allProbes = [];
                for(var i = 0; i < res.length; i++){
                    allProbes.push(new Molecule(res[i]));
                }
                self.probes(allProbes);
            }
        });
        return self.probes;
    });

    self.calculatedPI = ko.pureComputed(function(){
        if(self.PrincipalInvestigatorID){
            $.ajax("/user/" + self.PrincipalInvestigatorID, {
                cache: false,
                headers: {"Accept": "application/json"},
                success: function(res){
                    res = JSON.parse(res);
                    res = new User(res);
                    self.principal_investigator(res);
                }
            });
        }
        return self.principal_investigator;
    });

    self.calculatedUsers = ko.pureComputed(function(){
        if(self.id){
            self.getAccountUsers();
        }

        return self.users;
    });

    self.getAccountUsers = function(){
        return $.ajax("/account/" + self.id + "/users", {
                cache: false,
                headers: {"Accept": "application/json"},
                success: function(res){
                    res = JSON.parse(res);
                    var users = [];
                    for(var i = 0; i < res.length; i++){
                        var u = new User(res[i]);
                        if(u.UserID == self.primary_contact_id){
                            u.isPrimaryContact(true);
                        }
                        users.push(u);
                    }
                    users = _.sortBy(users, function(user){
                        return !user.isPrimaryContact();
                    });
                    self.users(users);
                }
            });
    }

    self.save = function(){
        return self.record.save("/account/create").success(function(res){
            if(res.id){
                self.record.id(res.id);
                self.record.id.valueHasMutated();
            }
        });
    }

    self.hasUsers = ko.pureComputed(function(){
        var users = self.users();
        return users.length > 0;
    });

    self.contact_us_ctrl = ko.observable();
    self.contactUs = function(){
        if(self.contact_us_ctrl()){
            self.contact_us_ctrl().show();
        }
    }

    self.autofillLocation = function(){
        var geocoder = new google.maps.Geocoder();
        var address = self.record.City() + " " + self.record.State() + " " + self.record.Address() + " " + self.record.ZipCode();
        self.searchingCoords(true);
        geocoder.geocode({'address': address}, function(results, status) {
            if (status === google.maps.GeocoderStatus.OK) {
                var results = results[0];
                var location = results.geometry.location;
                self.record.Latitude(location.lat());
                self.record.Longitude(location.lng());
            }
            self.searchingCoords(false);
        });
    }
}

function initAccounts(accounts_details){
    var accounts = [];
    for( var i=0; i < accounts_details.length; i++ ){
        accounts.push(new Account(accounts_details[i]));
    }
    return accounts;
}

function loadAccounts(){
    var url = "/account";
    var promise = $.ajax({url: url,
                          headers:{'Accept': 'json'}
    });
    return promise;
}
