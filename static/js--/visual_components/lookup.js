var Lookup = function(params){
        var self = this;
        self.selectionLocked = ko.observable(false);
        self.name = ko.observable();
        self.showLookup = ko.observable(true);
        self.adminControls = !params.standardUser;
        if(params.lookupRef){
            params.lookupRef({name: self.name, selectionLock: self.selectionLocked});
        }
        self.hintsMethod = params.hints;// Expected is a method that takes in what is typed and returned is the hints
        self.showHints = self.hintsMethod != null;
        self.hints = ko.observableArray();
        self.doSelectHint = params.selectHint;
        self.sObjectType = params.sObjectType;
        self.record = params.record;
        self.column = params.column;
        self.doSearch = params.doSearch;

        self.numMatches = ko.pureComputed(function(){
            var hints = self.hints();
            return hints.length;
        });

        self.displayLink = params.displayLink;
        self.displayHints = ko.observable();
        self.routing_lookups = {"Sequences": "sequence","Components": "component", "Account" : "account", "Molecules": "probe"};

        self.searchTxt = ko.observable("");
        self.searchResults = ko.observableArray();
        self.searchModalVisible = ko.observable(false);

        self.parent_id = ko.pureComputed(function(){
            var col = self.column;
            if(self.record && self.record[col]){
                return self.record[col]();
            }
            return "";
        });

        self.lookup_url = ko.pureComputed(function(){
            var tableName = self.objectType();
            var url = self.routing_lookups[tableName] || tableName;
            return "/" + url + "/" + self.parent_id();
        });

        self.standardLookupUrl = ko.pureComputed(function(){
            var base_url = self.routing_lookups[self.sObjectType];
            return "/" + base_url + "/" + self.parent_id() + "/sObject/Name";
        });

        self.objectType = ko.pureComputed(function(){
            if(typeof self.sObjectType == "function"){
                return self.sObjectType();
            }
            return self.sObjectType;
        });

        self.setName = function(val){
            self.selectionLocked(true);
            self.name(val);
            setTimeout(function(){
                self.selectionLocked(false);
            }, 1000);
        }

        self.calculatedName = ko.computed(function(){
            if(self.record && self.record[self.column]){
                var parent = self.record[self.column]();
                if( parent ){
                    if(self.adminControls){
                        $.ajax("/admin/" + self.objectType() + "/" + parent + "/", {cache: false}).success(function(res){
                            if(res.lookup_name){
                                self.setName(res.lookup_name);
                                self.showLookup(true);
                            }
                        }).fail(function(err){
                            console.log(err);
                        });
                    }
                    else{
                        $.ajax(self.standardLookupUrl()).success(function(res){
                            self.setName(res);
                            self.showLookup(true);
                        }).fail(function(err){
                            console.log(err);
                        });
                    }
                }
            }
            return self.name;
        });

        self.name.subscribe(function(newVal){
            if(newVal != self.calculatedName() && !self.selectionLocked()){
                self.record[self.column](null);
            }
        });

        self.toggleShowSearch = function(){
            self.searchModalVisible(!self.searchModalVisible());
        }

        self.doHints = function(txt){
            self.hints([]);
            self.displayHints(true);
            var searchWord = txt.value;
            if(searchWord){
                self.hintsMethod(txt.value, self.hints);
            }
            return true;
        }

        self.selectHint = function(hint){
            self.hints([]);
            self.doSelectHint(self, hint);
        }

        self.name.subscribe(function(newVal){
            self.showLookup(false);
        });

        if(!self.doSearch){
            self.doSearch = function(){
                var url = "/admin/" + self.objectType() + "/search/" + self.searchTxt();
                $.ajax(url).success(function(res){
                    self.searchResults(res);
                }).fail(function(err){
                    console.log(err);
                });
            }
        }

        self.selectLookup = function(selectedRecord){
            var parentId = selectedRecord;
            if(selectedRecord.id){
                parentId = selectedRecord.id;
            }

            if(selectedRecord.name){
                self.name(selectedRecord.name);
            }
            self.showLookup(true);
            self.searchModalVisible(false);
            self.record[self.column](parentId);
        }

        self.hideHints = function(){
            setTimeout(function(){
                self.displayHints(false);
            }, 250);
        }

        self.doShowHints = function(){
            self.displayHints(true);
        }
    }

ko.components.register('lookup', {
    viewModel: function(params){
        return new Lookup(params);
    },
    template: {element: 'lookup-template'}
});