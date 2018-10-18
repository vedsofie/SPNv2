MoleculeDetailView = function(params){
    self = this;
    self.molecule = params.molecule;
    self.privateAccounts = ko.observableArray();
    self.loadingSequences = ko.observable(true);

    self.molecule.getSequences().success(function(res){
        self.loadingSequences(false);
    }).fail(function(){
        self.loadingSequences(false);
    });

    self.publicSequences = ko.pureComputed(function(){
        return _.filter(self.molecule.allSequences(), function(seq){
            return seq.IsDownloadable;
        });
    });

    self.cancel = function(){
        if(self.molecule.ID){
            window.location = '/probe/' + self.molecule.ID;
        }
        else{
            window.location = '/user/dashboard';
        }
    }

    self.privateSequences = ko.pureComputed(function(){
        return _.filter(self.molecule.allSequences(), function(seq){
            return !seq.IsDownloadable;
        });
    });

    self.privateSequenceAccounts = ko.pureComputed(function(){
        var acts = []
        $.ajax("/probe/" + self.molecule.ID + "/private_accounts/").success(function(res){
            for(var i = 0; i < res.length; i++){
                var act = new Account(res[i]);
                acts.push(act);
            }
            self.privateAccounts(acts);
        }).fail(function(err){
            alert(err);
        });
        return self.privateAccounts;
    });
}
