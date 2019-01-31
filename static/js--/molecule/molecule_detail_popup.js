MoleculeDetailPopup = function(params){
    var self = this;
    params = params || {};
    self.idPrefix = params.idPrefix || "";
    self.showBack = params.showBack || false;
    self.saveBtnText = params.saveBtnText || 'Save';
    if(params.btnText != null){
        self.btnText = params.btnText;
    }
    else{
        self.btnText = 'Create Probe';
    }
    self.showBtn = !params.hideButton;
    if(typeof params.doRevert === 'undefined' || params.doRevert==null){
        self.doRevert = true;
    }
    else{
        self.doRevert = params.doRevert;
    }
    $.extend(self, new PopupBox(params));

    self.molecule = params.molecule || new Molecule();
    var isNew = self.molecule.record.ID() == null;
    self.moleculeDetailViewModel = ko.observable(new MoleculeDetailViewModel({molecule: self.molecule, idPrefix: self.idPrefix}));
    self.doClose = self.close;
    self.stayOnPage = params.stayOnPage || false;

    self.revert = function(){
        self.molecule.record.revert(self.molecule);
    }

    self.save = function(){
        if(self.molecule.record.valid()){
            self.molecule.save().success(function(res){
                var moleculeId = res.ID;
                var synomynsSaved = self.moleculeDetailViewModel().synomynsKeywordViewModel.save("Molecules", moleculeId);
                var keywordsSaved = self.moleculeDetailViewModel().keywordsViewModel.save("Molecules", moleculeId);
                var bothSaved = synomynsSaved != null && keywordsSaved != null;
                var redirect_url = "/probe/" + moleculeId;
                //  console.log(redirect_url);

                if(synomynsSaved == null && keywordsSaved == null){
                    self.redirect(redirect_url);
                }
                else if(bothSaved){
                    var saved = 0;
                    var error = false;
                    synomynsSaved.success(function(){saved++}).fail(function(){error=true});
                    keywordsSaved.success(function(){saved++}).fail(function(){error=true});
                    var poll = setInterval(function(){
                        if(saved == 2){
                            self.redirect(redirect_url);
                        }
                        else if(error){
                            alert("Failed to save keywords");
                            clearInterval(poll);
                        }
                    }, 500);
                }
                else{
                    var promise = synomynsSaved || keywordsSaved;
                    promise.success(function(){
                        self.redirect(redirect_url);
                    }).fail(function(err){
                        alert("Failed to save keywords");
                    });
                }
            }).fail(function(err){
                console.log(err);
            });
        }
    }

    self.cancel = function(){
        if(self.molecule.ID){
            window.location = '/probe/' + self.molecule.ID;
        }
        else{
            window.location = '/user/dashboard';
        }
    }

    self.redirect = function(url){
        self.close();
        if(!self.stayOnPage){
            window.location = url;
        }
    }

    self.close = function(){
        self.doClose();
        self.molecule.filterKeywords();
        if(self.doRevert){
            self.molecule.record.revert(self.molecule);
        }
    }
}
