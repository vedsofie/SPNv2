AccountDetailViewModel = function(params){
    var self = this;
    self.account = params.account;
    self.edit = ko.observable(true);
    self.canToggle = ko.observable(false);
    self.toggleEditMode = function(){
        console.log("No function");
    }
}
