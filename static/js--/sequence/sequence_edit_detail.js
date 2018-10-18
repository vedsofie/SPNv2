SequenceDetailViewModel = function(params){
    var self = this;
    self.sequence = params.sequence || new Sequence();
    self.edit = ko.observable(true);
    self.idPrefix = params.idPrefix || "";
    self.moleculeSearch = new MoleculeSearch({noKeywords: true});
    self.canToggle = ko.observable(false);
    self.moleculeIsNew = false;

    self.lookupRef = ko.observable();

    self.toggleEditMode = function(){
        console.log("No function");
    }

    self.moleculeDetailPopup = new MoleculeDetailPopup({btnText: "",
                                                        saveBtnText: "Submit",
                                                        idPrefix: self.idPrefix,
                                                        showBack: true,
                                                        molecule: new Molecule({}),
                                                        stayOnPage: true,
                                                        doRevert: false});

    self.revert = function(){
        self.sequence.revert();
        self.lookupRef().selectionLock(true);
        self.lookupRef().name("");
        self.lookupRef().selectionLock(false);
        self.moleculeDetailPopup.revert();
    }

    self.setMoleculeName = function(){
        var editor = CKEDITOR.instances['molecule_formula_editor_name_' + self.idPrefix + '_' +  self.moleculeDetailPopup.molecule.ID];
        editor.setData(self.lookupRef().name());
    }

    self.getMoleculeHints = function(txt, hints){
        self.moleculeDetailPopup.molecule.record.Name(txt);
        self.moleculeSearch.getHint(txt).success(function(res){
            hints([]);
            var hintResults = self.moleculeSearch.keywordHints();
            for(var i = 0; i < hintResults.length; i++){

                var keyword = hintResults[i];
                hints.push(keyword);
            }

        }).fail(function(err){
            console.log(err);
        });
    }

    // This gets called when the molecule is successfully saved
    self.moleculeDetailPopup.molecule.record.ID.subscribe(function(newVal){
        if(newVal){
            self.sequence.record.MoleculeID(newVal);
            self.moleculeIsNew = true;
        }
    });

    self.selectHint = function(hintText, hint){
        var moleculeid = hint.molecule_id;
        hintText.selectLookup({id: moleculeid, name: hint.master_name});
        self.moleculeIsNew = false;
        self.sequence.record.MoleculeID(moleculeid);
    }

    self.uploadSequence = function(ele){
        var file = ele.files[0];
        self.sequence.sequenceFile(file);
    }

    self.canClearSequenceFile = ko.pureComputed(function(){
        return self.sequence.record.IsDownloadable() || self.sequence.sequenceFile();
    });

    self.deleteSequenceFile = function(){
        if(self.sequence.sequenceFile){
            self.sequence.sequenceFile(null);
        }

        if(sequence.record.IsDownloadable()){
            applicationConfirmation.prompt("Are you sure you want to delete your downloadable sequence?\n\n" +
                                           "This cannot be undone", self.doDeleteSequenceFile);
        }
    }

    self.deleteStrategy = function(){
        if(self.sequence.chemistryStrategyFile()){
            self.sequence.chemistryStrategyFile(null);
        }
        if(sequence.record.hasReactionScheme()){
            applicationConfirmation.prompt("Are you sure you want to delete your reaction scheme?\n\n" +
                                           "This cannot be undone", self.doDeleteReactionScheme);
        }
    }

    self.doDeleteReactionScheme = function(doDelete){
        if(doDelete){
            self.sequence.deleteStrategy();
        }
    }

    self.doDeleteSequenceFile = function(doDelete){
        if(doDelete){
            self.sequence.deleteSequenceFile();
        }
    }
}