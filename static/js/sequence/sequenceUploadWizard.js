var SequenceUploadWizard = function(params){
    var self = this;
    self.visible = ko.observable(false);
    self.moleculeSearch = ko.observable(new MoleculeSearch({"searchType":"local"}));
    self.selectedMolecule = ko.observable();
    self.keywords = ko.observableArray();
    self.newKeyword = ko.observable("");
    self.displayKeywords = ko.observable(false);
    self.displayUpload = ko.observable(false);
    self.displaySearch = ko.observable(false);
    self.canMakeOnElixys = ko.observable();
    self.sequenceFile = ko.observable();
    if(params.defaultName){
        self.defaultName = params.$raw.defaultName()();
    }
    else{
        self.defaultName = "";
    }

    self.afterSubmitHandler = params.afterSubmitHandler;
    self.popupText = params.popupText || "New Synthesis";

    self.open = function(){
        self.visible(true);
    }
    self.close = function(){
        self.visible(false);
        self.clear();
    }
    self.setMakesOnElixys = function(canMakeOnEli){
        self.canMakeOnElixys(canMakeOnEli);
        if(!self.selectedMoleculeId()){
            self.displaySearch(true);
        }
        else if( !canMakeOnEli ){
            self.submit();
        }
        else{
            self.displayUpload(true);
        }
    }
    self.viewMolecule = function(res){
        if(res.ID){
            window.open('/probe/' + res.ID,'_target');
        }
        else if(res.CID){
            window.open('https://pubchem.ncbi.nlm.nih.gov/compound/' + res.CID, '_target');
        }
    }
    self.selectMolecule = function(res){
        self.selectedMolecule(res);
        self.displaySearch(false);
        if(self.canMakeOnElixys()){
            self.displayUpload(true);
        }
        else{
            self.submit();
        }
    }
    self.addKeyword = function(){
        self.keywords.push(self.newKeyword());
        self.newKeyword("");
    }
    self.clear = function(){
        self.keywords([]);
        self.moleculeSearch(new MoleculeSearch());
        self.displayKeywords(false);
        self.displayUpload(false);
        self.displaySearch(false);
        self.sequenceFile(null);
        self.canMakeOnElixys(null);
    }
    self.keywordsComplete = function(){
        self.displayUpload(true);
        self.displaySearch(false);
        self.displayKeywords(false);
    }

    if(!params.selectedMoleculeId){
        self.selectedMoleculeId = ko.pureComputed(function(){
            if(self.selectedMolecule()){
                return self.selectedMolecule().ID;
            }
            return null;
        });
    }
    else{
        self.selectedMoleculeId = ko.observable(params.selectedMoleculeId);
    }

    self.uploadSequence = function(element){
        self.sequenceFile(element.files[0]);
    }
    self.submit = function(){
        var file = self.sequenceFile();
        self.readFile(file, function(res){
            res = btoa(res);
            var seqName = self.defaultName || self.selectedMolecule().Name;
            $.ajax("/sequence/import", {method: "post",
                                        data: JSON.stringify({
                                            "Sequence": res,
                                            "keywords": self.keywords(),
                                            "MadeOnElixys": self.canMakeOnElixys(),
                                            "MoleculeID": self.selectedMoleculeId(),
                                            "sequenceName": seqName
                                        }),
                                        contentType: 'application/json',
                                        headers: {'Accept': 'application/json'}
                                        })
            .success(function(res){
                self.close();
                var sequenceID = res.SequenceID;
                if(self.afterSubmitHandler){
                    self.afterSubmitHandler(sequenceID);
                }
                else{
                    window.location = "/sequence/" + sequenceID;
                }
            }).fail(function(err){
                console.log(err);
            });
        });
    }

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
}

ko.components.register('new-sequence-wizard', {
    viewModel: function(params){
        return new SequenceUploadWizard(params);
    },
    template: {element: 'sequence_wizard_template'}
});
