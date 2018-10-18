ko.components.register('sobject-field', {
    viewModel: function(params){
        var self = this;
        self.record = params.record;
        self.col = params.column;
    },
    template: {element: 'sobject-field-template'}
});