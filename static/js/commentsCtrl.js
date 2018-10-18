function Comment(details){
    var self = this;
    $.extend(self, details);

    self.OwnerName = ko.observable("");
    self.CommentID = ko.observable(self.CommentID ? self.CommentID : "");
    self.Message = ko.observable(self.Message ? self.Message : "");
    self.viewReplies = ko.observable(false);
    self.canViewComments = ko.observable(false);
    self.canReply = ko.observable(false);
    self.doDeletion = ko.observable(false);
    self.Image = ko.observable();
    self.RenderType = ko.observable(details.RenderType);
    self.isSaving = ko.observable(false);
    self.savingErrors = ko.observable("");

    self.getOwnerName = function(){
        if( self.UserID ){
            $.ajax("/user/" + self.UserID + "/", {
                cache: false,
                headers: {"Accept": "application/json"},
                success: function(res){
                    var user = JSON.parse(res);
                    self.OwnerName(user['username']);
                }
            });
        }
    }

    self.save = function(){
        self.savingErrors("");
        var resp = validate({message: self.Message()}, {message: {length: {maximum: 3000}}});
        if(!resp){
            self.isSaving(true);
            return $.post("/comment/", {"Message": self.Message(),
                                 "Type": self.Type,
                                 "ParentID": self.ParentID}, function(res){
                res = JSON.parse(res);
                self.UserID  = res.UserID;
                self.CommentID(res.CommentID);
                self.RenderType("text");
                self.getOwnerName();
                self.isSaving(false);
            }).fail(function(err){
                self.isSaving(false);
            });
        }
        else{
            self.savingErrors(resp.message[0]);
        }
    }

    self.postImage = function(){
        self.isSaving(true);
        $.ajax("/comment/image", {method: "post",
                                  contentType: "application/json",
                                  data: JSON.stringify({
                                          "Type": self.Type,
                                          "ParentID": self.ParentID,
                                           "Image": self.Image()
                                  })
        }).success(function(res){
            self.UserID  = res.UserID;
            self.RenderType("image");
            self.CommentID(res.CommentID);
            self.getOwnerName();
            self.isSaving(false);
        }).fail(function(err){
            self.isSaving(false);
            alert(err);
        });
    }

    self.attachFile = function(attachment){
        applicationConfirmation.prompt("Are you sure you want to upload " + attachment.name + "?", function(doAttach){
            if(doAttach){
                self.isSaving(true);
                var formData = new FormData();
                formData.append('file', attachment, attachment.name);
                formData.append('ParentID', self.ParentID);
                formData.append('Type', self.Type);
                return $.ajax("/comment/attachment", {
                    method: 'post',
                    processData: false,
                    contentType: false,
                    data: formData
                }).success(function(res){
                    self.UserID  = res.UserID;
                    self.Message(res.Message);
                    self.CommentID(res.CommentID);
                    self.RenderType(res.RenderType);
                    self.getOwnerName();
                    self.isSaving(false);
                }).fail(function(err){
                    alert(err);
                    self.isSaving(false);
                });
            }
        })

    }

    self.attachmentName = ko.pureComputed(function(){
        var msg = JSON.parse(self.Message());
        console.log(self.Message());
        return msg['name'];
    });

    self.attachmentLink = ko.pureComputed(function(){
        var msg = JSON.parse(self.Message());
        return msg['url'];
    });

    self.delete_self = function(){
        applicationConfirmation.prompt( "Are you sure you want to delete this comment?", self.doDeletion);
    }

    self.canDelete = ko.pureComputed(function(){
        return runningUser.UserID == self.UserID || runningUser.RoleType == 'super-admin';
    });

    self.doDeletion.subscribe(function(confirmed){
        if(confirmed){
            $.ajax("/comment/" + self.CommentID() + "/", {
                method: "delete",
                success: function(res){
                    self.CommentID(null);
                }
            });
        }
    });

    self.toggleViewReplies = function(){
        self.viewReplies(!self.viewReplies());
    }

    self.checkForSave = function(data, evt){
        if(evt.keyCode == 13){
            /*The delay is to ensure ko has time to bind the last character*/
            setTimeout(self.save, 250);
        }
        return true;
    }

    self.displayDateTime = ko.pureComputed(function(){
        var dt = self.CreationDate;
        try{
            return moment(dt).fromNow();//format("MMM Do YYYY [at] h:mma");
        }
        catch(err){
            return null;
        }
    });

    self.getOwnerName();
}