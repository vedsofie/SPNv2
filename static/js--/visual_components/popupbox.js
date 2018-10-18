PopupBox = function(params){
    var self = this;
    params = params || {};
    self.title = params.title || "";
    self.visible = ko.observable(false);
    self.close = function(){
        self.visible(false);
    }
    self.open = function(){
        self.visible(true);
    }
}
