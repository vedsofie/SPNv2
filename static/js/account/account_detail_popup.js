var AccountDetailPopup = function(params){
    var self = this;
    self.btnText = params.btnText || 'Create Organization';
    $.extend(self, new PopupBox());
    self.account = params.account || new Account();
    self.showBtn = !params.hideButton;

    var isNew = self.account.record.id() == null;
    self.accountDetailViewModel = ko.observable(new AccountDetailViewModel({account: self.account}));
    self.userCreator = ko.observable();
    self.doClose = self.close;

    self.close = function(){
        self.doClose();
        self.account.record.revert(self.account);
    }

    self.cancel = function(){
        if(self.account.id){
            window.location = '/account/' + self.account.id;
        }
        else{
            window.location = '/user/dashboard';
        }
    }

    self.save = function(){
        if(self.account.record.valid()){
            self.account.save().success(function(res){
                self.doClose();
                var actId = res.id;
                window.location = "/account/" + actId + "/";
            }).fail(function(err){});
        }
    }
}

