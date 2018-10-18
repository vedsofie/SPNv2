var BaseHintSearch = function(self, params){
    params = params || {};
    self.text = params.text || ko.observable("");
    self.keywordHints = ko.observableArray();
    self.showHints = ko.observable(false);
    self.placeHolder = params.placeHolder || "";
    self.redirect = params.redirect || false;
    self.matches = params.displayResults || ko.observableArray();

    self.search = function(data, evt){
        if(evt.keyCode == 13){
            self.doSearch();
        }
        else{
            self.keywordHints([]);
            var searchWord = self.text();
            if( searchWord.length >= 3){
                self.getHint(searchWord);
            }
        }
    }

    self.numMatches = ko.pureComputed(function(){
        var keys = self.keywordHints();
        return keys.length;
    });

    if(!self.doSearch){
        self.doSearch = function(){
            alert("you should override doSearch");
        }
    }

    if(!self.getHint){
        self.getHint = function(searchWord){
            alert("you should override getHint");
        }
    }

    self.hideHints = function(){
        setTimeout(function(){
            self.showHints(false);
        }, 250);
    }

    self.doShowHints = function(){
        if(self.keywordHints().length > 0){
            self.showHints(true);
        }
    }

    self.autoFillText = self.autoFillText ||
                                             function(match){
                                                    self.text(match.master_name);
                                                    self.doSearch(match.molecule_id);
                                             }
}

var MoleculeSearch = function(params){
    var self = this;
    var params = params || {};
    self.isSearching = ko.observable(false);
    if(typeof params.noKeywords !== 'undefined'){
        self.includeKeywords = !params.noKeywords;
    }
    else{
        self.includeKeywords = true;
    }

    self.hasSearched = ko.observable(false);
    self.keywordHints = ko.observableArray();

    self.noResultsFound = ko.pureComputed(function(){
        return self.matches().length == 0 && !self.isSearching() && self.hasSearched();
    });


    self.doSearch = function(molecule_id){
        self.keywordHints([]);
        self.isSearching(true);
        self.hasSearched(true);
        var keyword = self.text();
        var actionType = self.redirect ? "redirect" : "ajax";

        $.ajax("/probe/list/?includeKeywords=" + self.includeKeywords,{
                                   contentType: "application/json",
                                   headers: {"Accept": "application/json"},
                                   cache: false,
                                   method: "post",
                                   data: JSON.stringify({"keyword": keyword,
                                                         "molecule_id": molecule_id,
                                                         "actionType": actionType})
                                   })
        .success(function(res){
            if(res.redirect_to){
                window.location = res.redirect_to;
            }
            else{
                self.isSearching(false);
                var moles = [];
                for(var i = 0; i < res.length; i++){
                    var mole = res[i];
                    var molecule = new Molecule(res[i]);
                    moles.push(molecule);
                }
                console.log(moles);
                self.matches(moles);
            }
        }).fail(function(err){
            self.isSearching(false);
        });
    }

    self.getHint = function(searchWord){
        return $.ajax("/probe/hint/" + searchWord + "?includeKeywords=" + self.includeKeywords, {cache: false}).success(function(res){
            self.showHints(true);
            self.keywordHints(res);
        }).fail(function(err){
            console.log(err);
        });
    }

    var search = new BaseHintSearch(self, params);
    $.extend(self, search);
}

PubChemSearch = function(params){
    var self = this;

    self.doSearch = function(keyword){
        self.text(keyword.Keyword);
        var txt = encodeURIComponent(self.text());
        self.matches(keyword.CID);
        //self.showHints(false);
    }

    self.getHint = function(searchWord){
        /*self.showHints(true);
        searchWord = encodeURIComponent(searchWord);
        $.ajax("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" + searchWord + "/cids/JSON?name_type=word").success(function(res){
            var idList = res.IdentifierList
            var cids = idList ? idList.CID : [];
            cids = cids.slice(0, 20);
            var cidCommaSep = cids.join();
            $.ajax("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/" + cidCommaSep + "/description/JSON").success(function(res){
                var infoList = res.InformationList;
                var info = infoList.Information;
                for(var i = 0; i < info.length; i++){
                    var chemical = info[i];
                    if(chemical.Title){
                        var key = new Keyword({Keyword: chemical.Title, CID: chemical.CID});
                        self.keywordHints.push(key);
                    }
                }
            }).fail(function(err){
                console.log(err);
            });
        }).fail(function(err){
            //console.log(err)
        });*/
    }

    self.autoFillText = function(match){
        self.doSearch(match);
    }

    var search = new BaseHintSearch(self, params);
    $.extend(self, search);
}
