ContactUsCtr = function(params){
        var self = this;

        if(typeof params.contact !== 'function'){
            self.to_contact_name = ko.observable(params.contact);
        }
        else{
            self.to_contact_name = params.contact;
        }
        self.message = params.Message || "";
        self.to_contact_url = ko.observable(params.contact_url);
        self.runningUser = ko.observable();
        self.showSend = true;
        if(params.hideSend){
            self.showSend = false;
        }

        $.ajax("/user/me", {
            method: "GET",
            cache: false,
            headers: {"Accept": "application/json"},
            success: function(res){
                self.runningUser(new User(res));
                self.myMessage.record.name(self.runningUser().name());
                self.myMessage.record.email(self.runningUser().Email);
            }
        });

        self.runningUserAccount = ko.pureComputed(function(){
            if(self.runningUser()){
                var act = self.runningUser().calculated_account()();
                if(act){
                    return act;
                }
                return {name: ""};
            }
            return {name: ""};
        });

        self.send = function(){
            if(!self.myMessage.record.valid()){
                return;
            }
            self.myMessage.record.isSaving(true);
            return $.ajax(self.to_contact_url(), {
                                         method: "post",
                                         contentType: "application/json",
                                         data: JSON.stringify(self.myMessage.record)
                                         })
            .success(function(res){
                self.myMessage.record.message(self.message);
                self.myMessage.record.isSaving(false);
            }).fail(function(res){
                self.myMessage.record.isSaving(false);
                alert('Failed to make contact with ' + self.to_contact_name());
            });
        }

        ToSendMessage = function(details){
            var self = this;
            $.extend(self, details);
            self.record = new Record(self);
            self.record.addColumn("name", true, {presence: true});
            self.record.addColumn("email", true, {presence: true, email: true});
            self.record.addColumn("message", true, {presence: true});
        }

        self.myMessage = new ToSendMessage({name: "",
                                            message: self.message,
                                            email: ""});
}

ko.components.register('contact-us', {
    viewModel: function(params){
        return new ContactUsCtr(params)
    },
    template: {element: 'contact-template'}
});

var ContactUsPopupCtrl = function(params){
    var self = this;
    $.extend(self, new PopupBox());
    self.showOpenButton = !(params.hideOpenButton || false);
    self.btnText = params.btnText || "Request Information";
    params.hideSend = true;
    self.doClose = self.close;
    self.ctrl = new ContactUsCtr(params);

    self.send = function(){
        var promise = self.ctrl.send();
        if(promise){
            promise.success(function(res){
                console.log(res);
                self.doClose();
            }).fail(function(err){
                alert(err);
            });
        }
    }

    self.close = function(){
        self.ctrl.myMessage.record.revert(self.ctrl.myMessage);
        self.doClose();
    }
}

ko.components.register('contact-us-popup', {
    viewModel: function(params){return new ContactUsPopupCtrl(params);},
    template: {element: 'contact-us-popup-template'}
});

