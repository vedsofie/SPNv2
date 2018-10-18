ko.components.register('polymorphic-lookup', {
    viewModel: function(params){
        var self = this;
        self.record = params.record;
        self.column = params.column;
        self.availableSObjectTypes = self.column.types;
        self.displayLink = params.displayLink || false;
        var selectedObj = self.record[self.column.lookup_driver]();
        self.sObjectType = ko.observable(selectedObj);
        self.sObjectType.subscribe(function(newVal){
            self.record[self.column.name](null);
            self.record[self.column.lookup_driver](newVal);
        });
    },
    template: {element: "polymorphic-lookup-template"}
});