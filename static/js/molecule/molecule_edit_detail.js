MoleculeDetailViewModel = function(params){
    var self = this;
    self.molecule = params.molecule;
    self.idPrefix = params.idPrefix || "";
    self.edit = ko.observable(true);
    self.canToggle = ko.observable(false);
    self.toggleEditMode = function(){
        console.log("No function");
    }
    var keys = self.molecule.calculatedKeywords();
    self.molecule.pubchemSearch.matches.subscribe(function(newVal){
        self.molecule.record.CID(newVal);
    });

    self.synomynsKeywordViewModel = new KeywordListPopupCtrl({zIndex: 30,
                                                       useFormulaEditor: true,
                                                       keywords: self.molecule.synonyms,
                                                       btnText: 'Synonyms',
                                                       addKeywordTxt: "Add",
                                                       Category: "Synonym"});

    self.keywordsViewModel = new KeywordListPopupCtrl({zIndex: 30,
                                                       keywords: self.molecule.keywordKeywords,
                                                       btnText: 'Keywords',
                                                       addKeywordTxt: "Add",
                                                       Category: "Keyword"});
}
