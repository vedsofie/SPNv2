SequenceDetailPopup = function(params){
    var self = this;
    self.btnText = params.btnText || 'Create Sequence';
    $.extend(self, new PopupBox());
    self.sequence = params.sequence || new Sequence();
    self.idPrefix = params.idPrefix || "";
    self.showBtn = !params.hideButton;
    var isNew = self.sequence.record.SequenceID() == null;
    self.sequenceDetailViewModel = ko.observable(new SequenceDetailViewModel({sequence: self.sequence, idPrefix: self.idPrefix}));
    self.doClose =  self.close;

    self.save = function(){
        if(!self.sequence.record.valid()){
            return;
        }
        self.sequence.save().success(self.afterSaveSuccess);
    }

    self.afterSaveSuccess = function(res){
        var sequenceId = res.SequenceID;
        self.sequence.record.isSaving(false);

        if(sequenceId){
            window.location = "/sequence/" + sequenceId + "/?showThankyou=True";
        }
    }

    self.canSave = ko.pureComputed(function(){
        return true;
    });

    self.cancel = function(){
        if(self.sequence.SequenceID){
            window.location = '/sequence/' + self.sequence.SequenceID;
        }
        else{
            window.location = '/user/dashboard';
        }
    }

    self.readyToOpenMoleculeDialog = ko.pureComputed(function(){
        var molecule = self.sequenceDetailViewModel().moleculeDetailPopup;
        if(molecule){
            var id = molecule.molecule.record.ID();
            var sequencesMoleculeId = self.sequence.record.MoleculeID();
            molecule = molecule.molecule.record.Name();
            var moleculeNamed = molecule != "" && molecule != null;
            return moleculeNamed && sequencesMoleculeId == null;
        }
        return false;
    });

    self.openMoleculeDialog = function(){
        self.sequenceDetailViewModel().setMoleculeName();
        self.sequenceDetailViewModel().moleculeDetailPopup.open();
    }

    self.close = function(){
        self.doClose();
        self.sequenceDetailViewModel().revert();
    }
}