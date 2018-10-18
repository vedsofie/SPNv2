UserDetailViewModel = function(params){
    var self = this;
    self.user = params.usr;
    self.edit = ko.observable(true);
    self.canToggle = ko.observable(false);
    self.toggleEditMode = function(){
        console.log("No function");
    }
}
