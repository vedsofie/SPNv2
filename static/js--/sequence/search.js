SequenceSearchController = function(params){
    self = this;
    self.sequences = params.sequences;
    self.allSequences = params.allSequences;
    self.filteredBy = ko.observable("all");
    self.hideTextSearch = params.hideTextSearch || false;

    self.showSequencesMadeOnElixys = function(){
        self.filteredBy("madeOnElixys");
        self.sequences(_.filter(self.allSequences(), function(seq){
            return seq.MadeOnElixys;
        }));
    }

    self.showSequencesDownloadable = function(){
        self.filteredBy("downloadable");
        self.sequences(_.filter(self.allSequences(), function(seq){
            return seq.IsDownloadable;
        }));
    }

    self.showSequencesNotMadeOnElixys = function(){
        self.filteredBy("notMadeOnElixys");
        self.sequences(_.filter(self.allSequences(), function(seq){
            return !seq.MadeOnElixys;
        }));
    }

    self.showAllSequences = function(){
        self.filteredBy("all");
        self.sequences(self.allSequences());
    }
}

ko.components.register('sequence-search-bar', {
    viewModel: SequenceSearchController,
    template: {element: 'sequence-search-bar-template'}
});