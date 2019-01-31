function Sequence(details){
    var self = this;
    if(!details){
        details = {};
    }
    if(!parseInt(details.SynthesisTime)){
        details.SynthesisTime = 0;
    }
    if(!parseInt(details.NumberOfSteps)){
        details.NumberOfSteps = 0;
    }
    if(!details.MadeOnElixys){
        details.MadeOnElixys = false;
    }

    $.extend(self, details);

    validate.validators.termsAndConditionsApply = function(value, options, key, attributes) {
        if(options.self.sequenceFile() && !value){
            return "must be agreed upon to upload a sequence";
        }
    }

    self.initRecord = function(){
        self.record = new Record(self);
        self.record.addColumn("SequenceID");
        self.record.addColumn("UserID");
        self.record.addColumn("MoleculeID", true, {presence: {message: " cannot be blank; If this is a new probe, please create it prior to creating this sequence"},
                                                   isNumber: true,
                                                   });
        self.record.addColumn("Name", true, {presence: true, length: {maximum: 64}});
        self.record.addColumn("Comment", true, {length: {maximum: 255}});
        self.record.addColumn("MadeOnElixys", true);
        self.record.addColumn("IsDownloadable", true);
        self.record.addColumn("NumberOfSteps", true, {isInteger: true, numericality:{ greaterThanOrEqualTo: 0}});
        self.record.addColumn("Yield", true, {isNumber: true, numericality:{ greaterThanOrEqualTo: 0, lessThanOrEqualTo: 100}});
        self.record.addColumn("PurificationMethod", true, {presence: true,length: {maximum: 30}});
        self.record.addColumn("SynthesisModule", true, {presence: true});
        self.record.addColumn("SpecificActivity", true, {isNumber: true, numericality:{ greaterThanOrEqualTo: 0}});
        self.record.addColumn("StartingActivity", true, {isNumber: true, numericality:{ greaterThanOrEqualTo: 0}});
        self.record.addColumn("hasReactionScheme", true);
        self.record.addColumn("SynthesisTime", true, {isInteger: true, numericality:{ greaterThanOrEqualTo: 0}});
        self.record.addColumn("TermsAndConditions", true, {termsAndConditionsApply: {"self": self}});

        self.record.addColumn("SpecificActivityStandardDeviation", true, {isNumber: true, numericality:{ greaterThanOrEqualTo: 0}});
        self.record.addColumn("StartingActivityStandardDeviation", true, {isNumber: true, numericality:{ greaterThanOrEqualTo: 0}});
        self.record.addColumn("YieldStandardDeviation", true, {isNumber: true, numericality:{ greaterThanOrEqualTo: 0}});
        self.record.addColumn("SynthesisTimeStandardDeviation", true, {isInteger: true, numericality:{ greaterThanOrEqualTo: 0}});
        self.record.addColumn("NumberOfRuns", true, {isInteger: true, numericality:{ greaterThanOrEqualTo: 0, lessThanOrEqualTo: 100}});
    }

    self.initRecord(self);

    self.calculateMadeOnElixys = function(){
        var synthModule = self.record.SynthesisModule();
        self.record.MadeOnElixys(synthModule == 'SOFIE ELIXYS');
    }
    self.calculateMadeOnElixys();

    self.record.SynthesisModule.subscribe(function(newVal){
        self.calculateMadeOnElixys();
    });

    self.moduleOptions = ko.observableArray([self.record.SynthesisModule()]);

    self.termAndConditionAgreementCheckbox = ko.observable(details.TermsAndConditions || false);
    self.termsAndConditionsCanBeAltered = (self.termAndConditionAgreementCheckbox() == false);

    self.sequenceFile = ko.observable();
    self.chemistryStrategyFile = ko.observable();
    self.owner = ko.observable("Sequence Owner");
    self.running_user_is_following = ko.observable(false);
    self.reagents = ko.observableArray();
    self.account = ko.observable(new Account());
    self.accountName = ko.observable("");
    self.molecule = ko.observable();
    self.calculated_owner = ko.pureComputed(function(){
        console.log("Calculated owner bug");
        $.ajax("/user/" + self.UserID + "/", {
            method: "get",
            cache: false,
            headers: {"Accept": "application/json"},
            success: function(res){
                res = JSON.parse(res);
                var usr = new User(res);
                self.owner(usr.name());
            }
        });
        return self.owner;
    });

    self.accountUrl = ko.observable("#");

    self.getDetails = function(){
        return $.ajax("/sequence/" + self.SequenceID, {
            headers: {"Accept": "application/json"}
        }).success(function(res){
            $.extend(self, res);
            self.initRecord();
            for(col in self.record){
                if(typeof col == "function"){
                    col.valueHasMutated();
                }
            }
        }).fail(function(err){
            console.log(err);
            alert(err);
        });
    }

    self.termAndConditionAgreementCheckbox.subscribe(function(agreedTo){
        var currentTime = null;
        if(agreedTo){
            currentTime = (new Date).getTime() / 1000;
        }
        self.record.TermsAndConditions(currentTime);
    });

    self.deleteSequenceFile = function(){
        return $.ajax("/sequence/" + self.SequenceID + "/components", {method: "delete"}).success(function(res){
            self.IsDownloadable = false;
            self.record.IsDownloadable(false);
        });
    }

    self.calculatedModuleOptions = ko.pureComputed(function(){
        $.ajax('/sequence/module/list/').success(function(res){
            self.moduleOptions(res);
        }).fail(function(err){
            console.log(err);
        });
        return self.moduleOptions;
    });

    self.canSave = ko.pureComputed(function(){
        return self.record.Name() != "" && self.record.Name() != null &&
               self.record.PurificationMethod() != "" && self.record.PurificationMethod() != null &&
               self.record.MoleculeID() != null;
    });

    self.delete_self = function(){
        return $.ajax("/sequence/" + self.SequenceID + "/", {
            method: "delete"
        });
    }

    self.calculatedUserIsFollowing = ko.pureComputed(function(){
        $.ajax("/sequence/" + self.SequenceID + "/check_following/", {
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
        $.ajax("/sequence/" + self.SequenceID + "/unfollow/", {
            method: "delete",
            success: function(res){
                self.running_user_is_following(false);
            }
        });
    }

    self.follow = function(){
        $.ajax("/sequence/" + self.SequenceID + "/follow/", {
            method: "post",
            success: function(res){
                self.running_user_is_following(true);
            }
        });
    }

    self.calculatedReagents = ko.pureComputed(function(){
        var url = "/sequence/" + self.SequenceID + "/reagents";
        $.ajax(url, {cache: false}).success(function(res){
            var all = [];
            for(var i = 0; i < res.length; i++){
                var reg = res[i];
                if(reg.Name != ""){
                    all.push(reg);
                }
            }
            self.reagents(all);
        }).fail(function(err){
            console.log(err)
        });
        return self.reagents;
    });

    self.calculatedAccount = ko.pureComputed(function(){
        $.ajax("/sequence/" + self.SequenceID + "/account/", {method: "get", cache: false}).success(function(res){
            self.account(new Account(res));
            if(self.account()){

                self.accountUrl("/account/" + self.account().id + "/");
                self.accountName(self.account().name);
            }

        }).fail(function(err){
            console.log(err);
        });
    });

    self.calculatedAccountName = ko.pureComputed(function(){
        self.calculatedAccount();
        return self.accountName();
    });

    self.detailsURL = ko.computed(function(){
        return "/sequence/" + self.SequenceID + "/";
    });

    self.calculatedMoleculeName = ko.pureComputed(function(){
        $.ajax("/probe/" + self.MoleculeID + "/", {headers:{"Accept": "application/json"}, cache: false}).success(function(res){
            self.molecule(res);
        }).fail(function(err){
            console.log(err);
        });
        return self.moleculeName();
    });
    self.moleculeDisplayName = ko.pureComputed(function(){
        if(self.molecule()){
            return self.molecule().DisplayFormat;
        }
        return "";
    });

    self.calculatedMoleculeDisplayName = ko.pureComputed(function(){
        self.calculatedMoleculeName();
        return self.moleculeDisplayName();
    });

    self.moleculeName = ko.pureComputed(function(){
        if(self.molecule()){
            return self.molecule().Name;
        }
        else{
            return "";
        }
    });

    self.calculatedMoleculeImageUrl = ko.pureComputed(function(){
        if(self.MoleculeID){
            return "/probe/" + self.MoleculeID + "/image/";
        }
        return "";

    });

    self.canEdit = ko.pureComputed(function(){
        var usrRole = runningUser.RoleType;
        return usrRole == 'super-admin' ||
               runningUser.AccountID == self.account().id && usrRole == 'admin' ||
               self.record.UserID() == runningUser.UserID;
    });

    self.canClearStrategy = ko.pureComputed(function(){
        return self.chemistryStrategyFile() != null || self.record.hasReactionScheme();
    });

    self.uploadStrategy = function(ele){
        var file = ele.files[0];
        self.chemistryStrategyFile(file);
    }

    self.deleteStrategy = function(){
        self.chemistryStrategyFile(null);
        return $.ajax("/sequence/" + self.SequenceID + "/reaction_scheme", {method: "delete"}).success(function(res){
            self.record.hasReactionScheme(false);
            self.hasReactionScheme = false;
        });
    }

    self.reUpload = function(ele){
        var file = ele.files[0];
        self.readFile(file, function(res){
            res = btoa(res);
            $.ajax("/sequence/" + self.record.SequenceID() + "/update/", {method: 'post',
                                                                          contentType: 'application/json',
                                                                          data: JSON.stringify({
                                                                                'sequence': res
                                                                          })}).success(function(res){
                console.log("Saved")
            }).fail(function(err){
                alert(err);
            });
        });
    }

    self.canUpload = ko.pureComputed(function(){
        return self.record.MadeOnElixys();
    });

    self.readFile = function(file_name, callback){
        var file_reader = new FileReader();
        file_reader.onload = function(e) {
            var result = e.target.result;
            callback(result);
        }
        try{
            file_reader.readAsBinaryString(file_name);
        }
        catch(err){
            callback('');
        }
    }

    self.revert = function(){
        self.record.revert(self);
        self.sequenceFile(null);
    }

    self.save = function(){
        if(!self.sequenceFile() && !self.chemistryStrategyFile()){
            return self.record.save("/sequence/create").success(function(res){
                self.record.SequenceID(res.SequenceID);
            });
        }
        else{
            var attachment = self.sequenceFile();
            var values = {};
            values['sequence'] = attachment;
            values['SequenceMeta'] = JSON.stringify(self.record);
            values['reactionScheme'] = self.chemistryStrategyFile();
            return self.record.saveForm("/sequence/import", values).success(function(res){
                self.record.SequenceID(res.SequenceID);
            });
        }
    }

    function TheTermsAndConditionsPopup(){
        var self = this;
        $.extend(self, new PopupBox());

    }

    self.termsAndConditionsPopup = new TheTermsAndConditionsPopup();
}

function initSequences(sequences_details){
    var sequences = [];
    for( var i=0; i < sequences_details.length; i++ ){
        sequences.push(new Sequence(sequences_details[i]));
    }
    return sequences;
}

function loadSequences(){
    var url = "/sequence";
    var promise = $.ajax({url: url,
                          headers:{'Accept': 'json'}
    });
    return promise;
}

