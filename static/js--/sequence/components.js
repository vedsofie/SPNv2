ko.components.register('sequence-detail-popup', {
    viewModel: function(params){return new SequenceDetailPopup(params)},
    template: {element: 'sequence-detail-popup-template'}
});

ko.components.register('sequence-detail-card', {
    viewModel: function(params){
        var self = this;
        self.sequence = params.sequence;
        self.displayAccountName = params.displayAccountName;
    },
    template: {element: 'sequence_template'}
});
