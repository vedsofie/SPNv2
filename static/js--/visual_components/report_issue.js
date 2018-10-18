var Issue = function(details){
    var self = this;
    details = details || {};
    self.attachments = ko.observableArray();
    self.fileAttachments = ko.observableArray();

    $.extend(self, details);

    validate.validators.attachmentsRequired = function(value, options, key, attr){
        var obj = options['self'];
        if(obj.attachments().length > 0 || self.fileAttachments().length > 0){
            return;
        }
        else if(obj.record.assistanceRequest() == 'Instrument' || obj.record.assistanceRequest() == 'Software'){
            return "a sequence log or screen shots of the issue you are experiencing";
        }
    }

    self.isSaving = ko.observable(false);

    self.initRecord = function(){
        self.record = new Record(self);

        self.record.addColumn("message", true, {presence: true, length: {maximum: 3000}});
        self.record.addColumn("title", true, {presence: true, length:{maximum: 100}});
        self.record.addColumn("Color", true);
        self.record.addColumn("supportRequest", true, {presence: true});
        self.record.addColumn("elixysVersion", true, {presence: true, length:{maximum: 10}});
        self.record.addColumn("assistanceRequest", true, {presence: true});
        self.record.addColumn("pleaseAttach", true, {attachmentsRequired: {"self": self}});
    }
    self.initRecord(self);

    self.subscribeOnImageChange = function(attachment){
        attachment.image.subscribe(function(newVal){
            self.attachments.push(attachment);
            self.newImageAttachment(new Record({"name": "", "image": ""}));
            self.subscribeOnImageChange(self.newImageAttachment());
        });
    }
    self.attachImage = function(file){
        self.attachments.push(file);
    }
    self.attachFile = function(file){
        self.fileAttachments.push(file);
    }

    self.deleteFileAttachment = function(index){
        var attaches = [];
        for(var i = 0; i < self.fileAttachments().length; i++){
            if(i != index){
                attaches.push(self.fileAttachments()[i]);
            }
        }
        self.fileAttachments(attaches);
    }

    self.deleteImageAttachment = function(index){
        var attaches = [];
        for(var i = 0; i < self.attachments().length; i++){
            if(i != index){
                attaches.push(self.attachments()[i]);
            }
        }
        self.attachments(attaches);
    }

    self.save = function(){
        self.isSaving(true);
        var values = {};
        self.record.Color(goldenColors.getHsvGolden(0.5, 0.95));
        values['issue'] = JSON.stringify(self.record);
        values['numImages'] = self.attachments().length;
        values['numAttachments'] = self.fileAttachments().length;
        for(var i = 0; i < self.attachments().length; i++){
            var img = self.attachments()[i];
            values['image' + i] = img;
        }
        for(var i = 0; i < self.fileAttachments().length; i++){
            var img = self.fileAttachments()[i];
            values['attachment' + i] = img;
        }
        return self.record.saveForm("/issue/", values).success(function(res){
            self.id = res;
        }).fail(function(){
            self.isSaving(false);
        });
    }
}

ReportIssueCtrl = function(params){
    var self = this;
    $.extend(self, new PopupBox());
    self.showBtn = !params.hideButton;
    self.btnText = params.btnText || "Report Issue";
    self.issue = ko.observable(new Issue({message: "",title:""}));
    self.doClose = self.close;
    self.isSaving = ko.observable(false);

    self.reportIssue = function(){
        if(self.issue().record.valid()){
            self.isSaving(true);
            self.issue().save().success(function(res){
                $.notify("Thank-You, a case is being created for you.\nA representative at Sofie Biosciences will be in contact with you shortly.", "success");
                self.isSaving(false);
                self.doClose();
                setTimeout(function(){
                    window.location = '/user/dashboard?issue=' + (res.FollowerID);
                }, 2000);
            }).fail(function(err){
                console.log("Err");
                self.isSaving(true);
                console.log(err);
            });
        }
    }

    self.close = function(){
        var issue = self.issue();
        issue.attachments([]);
        issue.fileAttachments([]);
        issue.record.revert(issue);
        self.doClose();
    }
}

ko.components.register('report-issue-popup', {
    viewModel: function(params){
        return new ReportIssueCtrl(params)
    },
    template: {element: 'report-issue-popup-template'}
});