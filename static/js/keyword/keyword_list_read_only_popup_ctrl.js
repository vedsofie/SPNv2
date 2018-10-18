KeywordListReadOnlyPopupCtrl = function(params){
    var self = this;
    self.btnText = params.btnText || "View Keywords";
    self.zIndex = params.zIndex || 1;
    self.keywords = params.keywords || ko.observableArray();
    self.template = params.template;
    self.showTemplate = self.template != null;
    self.showBtn = !params.hideBtn && !self.template;
    self.parentId = params.parent_id;
    self.type = params.type;
    self.category = params.category;
    self.loading = ko.observable(false);
    $.extend(self, new PopupBox());

    self.loadKeywords = function(keywordType, parentId){
        self.keywords([]);
        self.loading(true);
        $.ajax("/keyword/" + keywordType + "/" + parentId + "/").success(function(res){
            for(var i = 0; i < res.length; i++){
                var keyword = res[i]
                keyword = new Keyword(keyword);
                if(keyword.Category == self.category){
                    self.keywords.push(keyword);
                }
            }
            self.loading(false);
        }).fail(function(err){
            self.loading(false);
        });
    }

    self.keywordCount = ko.pureComputed(function(){
        var keys = self.keywords();
        return keys.length;
    });

    self.open = function(){
        self.visible(true);
        self.loadKeywords(self.type, self.parentId);
    }

    if(params.autoCalculate){
        self.loadKeywords(self.type, self.parentId);
    }
}
