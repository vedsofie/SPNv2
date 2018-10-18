ko.components.register('molecule-detail-popup', {
    viewModel: function(params){return new MoleculeDetailPopup(params);},
    template: {element: 'molecule-detail-popup-template'}
});

ko.components.register('global-search', {
    viewModel: function(params){return new MoleculeSearch(params);},
    template: {element: 'moleculeSearch'}
});
