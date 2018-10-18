ko.components.register('notification-popup', {
    viewModel: function(params){
        var self = this;
        self.visible = ko.observable(params.visible || false);
        self.title = ko.observable(params.title || "");
        self.message = ko.observable(params.message || "");
    },
    template: {element: 'notification-popup-template'}
});
