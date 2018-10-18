function Molecule(details){
    var self = this;
    details = details || {};
    if(typeof details.Approved === 'undefined'){
        details.Approved = true;
    }
    $.extend(self, details);

    self.initRecord = function(){
        self.record = new Record(self);
        self.record.addColumn("ID");
        self.record.addColumn("Formula", true, {length: {maximum: 300}});
        self.record.addColumn("CID", true, {isInteger: true});
        self.record.addColumn("Name", true, {presence: true,length: {maximum: 300}});
        self.record.addColumn("Description", true, {length: {maximum: 530}});
        self.record.addColumn("Image", true, {presence: !self.record.ID()});
        self.record.addColumn("Color");
        self.record.addColumn("DisplayFormat");
        self.record.addColumn("CAS", true, {length: {maximum: 300}});
        self.record.addColumn("Isotope", true, {presence: true, length: {maximum: 100}});
        var runningUserDefined = typeof runningUser !== 'undefined';
        var canEditApproved = runningUserDefined && runningUser.RoleType == 'super-admin';
        self.record.addColumn("Approved", canEditApproved);
    }
    self.initRecord(self);
    self.pubchemSearch = new PubChemSearch({text: self.record.Name, placeHolder: "Probe Name"});
    self.sequences = ko.observableArray();
    self.allSequences = ko.observableArray();
    self.showMoreInfo = ko.observable(false);
    self.sequence_count = ko.observable("x");
    self.keywords = ko.observableArray();
    self.running_user_is_following = ko.observable(false);
    self.iMakeThisMolecule = ko.observable(false);
    self.synonyms = ko.observableArray();
    self.keywordKeywords = ko.observableArray();

    self.getSequences = function(){
        return $.ajax("/probe/" + self.ID + "/sequences", {cache: false}).success(function(res){
            self.sequences([]);
            for(var i = 0; i < res.length; i++){
                self.sequences.push(new Sequence(res[i]));
            }
            self.allSequences(self.sequences());
        }).fail(function(err){
            console.log("sequences failed to load");
            self.sequences([]);
        });
    }

    self.doDelete = function(yes){
        if(yes){
            $.ajax("/probe/" + self.ID + "/", {method: 'DELETE'}).success(function(res){
                window.location = '/';
            }).fail(function(err){
                console.log(err);
            });
        }
    }

    self.delete_self = function(){
        applicationConfirmation.prompt("Are you sure you want to delete this probe?\n\n" +
                                           "This cannot be undone", self.doDelete);
    }

    self.calculatedSequences = ko.pureComputed(function(){
        self.getSequences();
        return self.sequences;
    });

    self.calculatedIMakeThisMolecule = ko.pureComputed(function(){
        $.ajax("/probe/" + self.ID + "/do_i_make_this/", {
            headers: {'Accept': 'application/json'}
        }).success(function(res){
            self.iMakeThisMolecule(res);
        });
        return self.iMakeThisMolecule();
    });

    self.canEdit = ko.pureComputed(function(){
        return runningUser.RoleType == 'super-admin';
    });

    self.calculatedUserIsFollowing = ko.pureComputed(function(){
        $.ajax("/probe/" + self.ID + "/check_following/", {
            method: "get",
            cache: false,
            headers: {'Accept': 'application/json'},
            success: function(res){
                res = JSON.parse(res);
                self.running_user_is_following(res);
            }
        });
        return self.running_user_is_following();
    });

    self.unfollow = function(){
        $.ajax("/probe/" + self.ID + "/unfollow/", {
            method: "delete",
            success: function(res){
                self.running_user_is_following(false);
            }
        });
    }

    self.follow = function(){
        $.ajax("/probe/" + self.ID + "/follow/", {
            method: "post",
            success: function(res){
                console.log(res);
                self.running_user_is_following(true);
            }
        });
    }

    self.calculatedKeywords = ko.pureComputed(function(){
        if(self.ID){
            $.ajax("/probe/" + self.ID + "/keywords", {cache: false}).success(function(res){
                var keys = [];
                for(var i = 0; i < res.length; i++){
                    var key = res[i];
                    key.useFormulaEditor = (key.Category=='Synonym');
                    keys.push(new Keyword(key));
                }
                self.keywords(keys);
            }).fail(function(err){
                console.log(err);
            });
        }
        return self.keywords;
    });

    self.keywords.subscribe(function(newVal){
        self.filterKeywords();
    });

    self.filterKeywords = function(){
        self.calculateSynonyms();
        self.calculateKeywordsKeywords();
    }

    self.calculateSynonyms = function(){
        self.synonyms([]);
        var keys = self.keywords();
        var filtered = _.filter(keys, function(key){return key.Category == "Synonym";});
        self.synonyms(filtered);
    }

    self.calculateKeywordsKeywords = function(){
        self.keywordKeywords([]);
        var keys = self.keywords();
        var filtered = _.filter(keys, function(key){return key.Category == "Keyword"});
        self.keywordKeywords(filtered);
    }

    self.calculatedSequenceCount = ko.pureComputed(function(){
        $.ajax("/probe/" + self.ID + "/sequence_count", {cache: false}).success(function(res){
            self.sequence_count(res);
        });
        return self.sequence_count();
    });

    self.image_url = ko.pureComputed(function(){
        return "/probe/" + self.ID + "/image/";
    });

    self.toggleMoreInfo = function(){
        self.showMoreInfo(!self.showMoreInfo());
    }

    self.color = ko.pureComputed(function(){
        if(!self.Color){
            return goldenColors.getHsvGolden(0.5, 0.95);
        }
        else{
            return self.Color;
        }

    });

    self.handleNowMakingMolecule = function(newSequenceID){
        var seq = new Sequence({SequenceID:newSequenceID});
        seq.getDetails().success(function(){
            self.sequences.unshift(seq);
        });
        self.iMakeThisMolecule(true);
    }

    self.detailsURL = ko.computed(function(){
        return "/probe/" + self.ID + "/";
    });

    self.save = function(){
        return self.record.save("/probe/create").success(function(res){
            if(res.ID){
                self.record.ID(res.ID);
            }
        });
    }
}