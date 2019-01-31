KeywordListPopupCtrl = function(params){
    var self = this;
    self.tempIndex = 1;
    self.btnText = params.btnText || "Add Keywords";
    self.originalKeys = params.keywords || ko.observableArray();
    self.Category = params.Category;
    self.keywords = params.keywords || ko.observableArray();
    self.showBtn = !params.hideBtn;
    self.type = params.Type;
    self.parentId = params.ParentID;
    self.owned = params.allowSave;
    self.zIndex = params.zIndex || 1;
    self.newKeyword = ko.observable();
    self.useFormulaEditor = params.useFormulaEditor || false;
    self.keywordsToDelete = [];
    self.addKeywordBtnText = params.addKeywordTxt || "Add";
    $.extend(self, new PopupBox());

    self.save = function(keywordType, parentId){
        var savedResponse = self.doSaveModifiedKeywords(keywordType, parentId);
        var deleteResponse = self.doDeleteOldKeywords();
        if(self.owned){
            self.close();
            window.location.reload();
        }
        return deleteResponse || savedResponse;
    }
    self.doSaveModifiedKeywords = function(keywordType, moleculeId){
        var newKeywords = self.keywordsToCreate();
        var keys = [];
        for(var i = 0; i < newKeywords.length; i++){
            var key = newKeywords[i];
            key.record.Type(keywordType);
            key.record.ParentID(moleculeId);
            keys.push(key.record);
        }

        if(newKeywords.length > 0){
            return $.ajax("/keyword/", {
                                 method: "post",
                                 contentType: "application/json",
                                 headers: {"Content-Type": "application/json",
                                           "Accept": "application/json"},
                                 data: JSON.stringify({"keywords": keys})}).success(function(res){
                console.log(res);
            }).fail(function(err){
                console.log(err);
            });
        }
    }

    self.doDeleteOldKeywords = function(){
        var keywordsToDel = self.keywordsToDelete;

        if(keywordsToDel.length){
            return $.ajax("/keyword/delete", {
                method: "post",
                contentType: "application/json",
                headers: {"Accept": "application/json"},
                data: JSON.stringify({"keywordIds": keywordsToDel})
            }).success(function(res){
                console.log(res);
            }).fail(function(err){
                console.log(err);
            });
        }
    }

    self.delete = function(keyword){
        var toDeleteId = keyword.record.KeywordID();
        var toDeleteIndex = keyword.index();

        self.keywords.remove(function(keyword){
            if( toDeleteId ){
                var willRemove = keyword.record.KeywordID() == toDeleteId;
                if(willRemove){
                    self.keywordsToDelete.push(toDeleteId);
                }
                return willRemove;
            }
            else if(toDeleteIndex){
                return keyword.index() == toDeleteIndex;
            }
            else{
                return false;
            }
        });
    }

    self.clear = function(){
        self.keywords([]);
    }

    self.addKeyword = function(){

        var key = self.newKeyword().record.Keyword();
        if(key && key != "" ){

            self.newKeyword().index(self.tempIndex);
            self.keywords.unshift(self.newKeyword());

            self.tempIndex++;
            self.createNewKeyword();
        }
    }

    self.createNewKeyword = function(keyword){
        self.newKeyword(new Keyword({Category: self.Category,
                                     useFormulaEditor: self.useFormulaEditor}));

        if(keyword){
            self.newKeyword().record.Keyword(keyword);
        }

    }

    self.keywordsToCreate = function(){
        var toCreate = [];
        for(var i = 0; i < self.keywords().length; i++){
            var key = self.keywords()[i];
            if(key.record.KeywordID() == null || key.record.isDirty()){
                toCreate.push(key);
            }
        }
        return toCreate;
    }

    self.checkAddKeyword = function(data, event){
        if(event.keyCode == 13){
            self.addKeyword();
            var elementID = self.newKeyword().htmlID;
            $("#" + elementID).focus();
        }
        return true;
    }

    self.keywordsToUpdate = function(){
        var toUpdate = [];
        for(var i = 0; i < self.keywords().length; i++){
            var key = self.keywords()[i];
            if(key.record.KeywordID() != null && key.record.isDirty()){
                toUpdate.push(key);
            }
        }
        return toUpdate;
    }
    self.createNewKeyword();
}