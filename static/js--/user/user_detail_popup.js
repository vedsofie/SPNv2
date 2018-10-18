UserDetailPopupCtrl = function(params){
    var self = this;

    $.extend(self, new PopupBox());
    self.openPopupButtonTemplate = params.openPopupButtonTemplate || "user-edit-button-standard";
    self.passwordResetRequired = params.passwordResetRequired || false;
    self.showBtn = !params.hideButton;
    self.doClose = self.close;
    if(!params.popupCtrl){
        self.btnText = params.btnText || 'Create User';
    }
    else{
        self.btnText = '';
        params.popupCtrl(self);
    }

    var actId = null;
    if(params.AccountID){
        actId = typeof params.AccountID == 'function' ? params.AccountID() : params.AccountID;
    }
    self.doOpen = self.open;

    self.open = function(){
        if(self.user.canEdit()){
            window.location = '/user/' + self.user.UserID + '/edit/';
            //self.doOpen();
        }
    }

    self.user = params.user || new User({AccountID:actId});
    var isNew = self.user.record.UserID() == null;
    self.userDetailViewModel = ko.observable(new UserDetailViewModel({usr: self.user}));

    self.save = function(){
        if(self.user.record.valid()){
            var promise = self.user.save();
            promise.success(function(res){
                self.close();
                if(!self.passwordResetRequired){
                    window.location = '/account/' + self.user.record.AccountID() + '/';
                }
            });
            return promise;
        }
        return null;
    }

    self.cancel = function(){
        if(self.user.AccountID){
            window.location = '/account/' + self.user.AccountID;
        }
        else{
            window.location = '/user/dashboard';
        }
    }

    self.close = function(){
        self.doClose();
        self.user.record.revert(self.user);
    }

    if(self.passwordResetRequired){
        self.visible(true);
    }
}
