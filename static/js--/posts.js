ko.components.register('posts', {
    viewModel: function(params){
        var self = this;
        self.FollowingID = params.record ? params.record.FollowingID : 'undefined';
        self.ReadOnly = params.record ? params.record.ReadOnly : false;
        self.record = params.$raw.record;
        self.uniqueImageUploadId = 'comment-image-' + self.FollowingID;

        if(!self.record){
            self.record = ko.observable({'Type': params.type,
                                         'OwnerID': params.parent_id,
                                         'EmailSubscribed': ko.observable(false)});
        }

        self.new_comment = ko.observable(new Comment({ParentID: self.record().OwnerID, Type: self.record().Type}));
        self.enabledMinimizing = params.enabledMinimizing || false;
        self.hasNotifications = ko.observable(self.record().hasNotifications || false);
        self.isExpanded = ko.observable(!self.enabledMinimizing ? true : (self.isExpanded || false));

        self.loading = ko.observable(false);
        self.canReply = ko.observable(true);
        self.offset = 0;
        self.canUnfollow = params.record && params.record.CanUnfollow || false;
        self.showContext = ko.observable(false);
        self.canClose = params.record && params.record.CanClose || false;
        if(params.noTitle){
            self.title = "";
        }
        if(typeof params.parent_id === "function"){
            self.parent_id = params.parent_id();
        }
        else{
            self.parent_id = params.parent_id;
        }
        self.type = params.type;
        self.comments = ko.observableArray([]);

        self.hasMore = ko.observable(false);

        self.postType = ko.computed(function(){
            switch(self.record().Type){
                case 'Sequences':
                    return 'Sequence';
                case 'Molecules':
                    return 'Probe';
                case 'Forums':
                    if(self.record().SubType == "FieldService"){
                        return "Field Service";
                    }
                    else{
                        return 'Sofie';
                    }
                default:
                    return '';
            }
        });

        self.canUnsubscribe = self.postType() == 'Field Service';

        self.postIcon = ko.pureComputed(function(){
            var postType = self.postType();
            switch(postType){
                case 'Sequence':
                    return "/static/img/sequence_icon.png";
                case 'Probe':
                    return "/static/img/probe_icon.png";
                case 'Field Service':
                    return "/static/img/support_icon.png";
                default:
                    return null;
            }
        });

        self.commentCount = ko.observable(0);
        self.calculatedCommentCount = function(){
            $.ajax("/comment/" + self.record().Type + "/" + self.record().OwnerID + "/count/").success(function(res){
                self.commentCount(res);
            });
            return self.commentCount();
        }

        self.isExpanded.subscribe(function(isOpen){
            if(isOpen){
                self.findComments();
            }
        });

        self.calculatedCanReply = ko.pureComputed(function(){
            if(self.record().FollowingID && self.record().Type == 'Forums'){
                $.ajax("/issue/" + self.record().FollowingID + '/can_reply').success(function(res){
                    self.canReply(res);
                });
            }
            return self.canReply();
        });

        self.isSaving = ko.pureComputed(function(){
            var newestComment = self.new_comment();
            return newestComment.isSaving();
        });

        self.bind_new_comments = function(){
            self.new_comment_binding = self.new_comment().CommentID.subscribe(function(newVal){
                self.offset += 1;
                self.commentCount(self.commentCount()+1);
                self.new_comment_binding.dispose();
                var newlyCreatedComment = self.new_comment();
                self.bind_delete_comment(newlyCreatedComment);
                self.comments.push(newlyCreatedComment);
                self.new_comment(new Comment({ParentID: self.record().OwnerID, Type: self.record().Type}));
                self.bind_new_comments();
            });
        }
        self.bind_delete_comment = function(comment){
            comment.CommentID.subscribe(function(newVal){
                if(!newVal){
                    self.commentCount(self.commentCount()-1);
                    var refreshedComments = [];
                    for(var i = 0; i < self.comments().length; i++){
                        if(comment !== self.comments()[i]){
                            refreshedComments.push(self.comments()[i]);
                        }
                    }
                    self.comments(refreshedComments);
                }
            });
        }

        self.postImageComment = function(){
            self.new_comment().postImage();
        }

        self.toggleExpanded = function(){
            if(self.enabledMinimizing){
                self.isExpanded(!self.isExpanded());
            }
        }

        self.subTitleMarkup = ko.observable(params.subTitleMarkup || "");

        self.bind_new_comments();
        if(params.ref){
            params.ref(self);
        }

        self.new_title = function(record) {
            var title = self.record().Title
            title = title.replace('<p>', '')
            title = title.replace('</p>', '')
            title = title.replace('<sup>', '')
            title = title.replace('</sup>', '')
            return title
        }

        self.unsubscribe = function(){
            var doSubscribe = self.record().EmailSubscribed() ? 'unsubscribe' : 'subscribe';
            applicationConfirmation.prompt("Are you sure you want to " + doSubscribe + " to email notifications for " + self.new_title(self.record().Title) + "?", function(confirmed){
                if(confirmed){
                    $.ajax("/issue/toggle/unsubscribe/" + self.FollowingID + "/").success(function(res){
                        location.reload();
                    }).fail(function(err){
                        console.log(err);
                    });
                }
            });
        }

        self.unfollow = function(){
            applicationConfirmation.prompt("Are you sure you want to unfollow " + self.new_title(self.record().Title) + "?", function(confirmed){
                if(confirmed){
                    $.ajax("/issue/unfollow/" + self.FollowingID).success(function(res){
                        if(self.record().Type == "Molecules"){
                            window.location = '/user/dashboard?myprobes=true';
                        }else if(self.record().Type == "Sequences") {
                            window.location = '/user/dashboard?mysequences=true';
                        }else {
                            location.reload();
                        }
                    }).fail(function(err){
                        console.log(err);
                    });
                }
            });
        }

        self.toggleContextMenu = function() {
            if(self.record().RedirectURL || self.canUnsubscribe){
                self.showContext(!self.showContext());
            }
        }

        self.hideContextMenu = function() {
            setTimeout( function() {
                self.showContext(false);
            }, 300);
        }

        self.close = function(){
            applicationConfirmation.prompt("Are you sure you want to close " + self.new_title(self.record().Title) + "?", function(confirmed){
                if(confirmed){
                    $.ajax("/issue/close/" + self.FollowingID).success(function(res){
                        location.reload();
                    }).fail(function(err){
                        console.log(err);
                    });
                }
            });
        }

        self.titleLink = params.titleLink;
        self.commentOrderOldestFirst = params.commentOrderOldestFirst;
        self.isChildPost = params.isChildPost || false;
        self.title = params.title || "Comments";
        self.loading = ko.observable(false);
        self.offset = 0;
        if(params.noTitle){
            self.title = "";
        }
        self.comments = ko.observableArray([]);

        self.hasMore = ko.observable(false);

        this.findComments = function(){
            self.loading(true);
            $.ajax("/comment/" + self.record().Type + "/" + self.record().OwnerID + "/comments?offset=" + self.offset, {
                headers: {"Accept": "application/json"},
                cache: false
            }).success(function(res){
                var comments = res['comments'];
                self.hasMore(res['has_more']);
                self.offset += comments.length;
                for( var i = 0; i < comments.length; i++ ){
                    var comment = new Comment(comments[i]);
                    self.comments.push(comment);
                    self.bind_delete_comment(comment);
                    var hasSubComments = true;
                    comment.canReply(!self.isChildPost && hasSubComments);
                }
                self.loading(false);

            }).fail(function(err){
                self.loading(false);
            });
        }

        if(self.isExpanded()){
            self.findComments();
        }

    },
    template: {element: 'post-template'}
});

ko.components.register('posts-popup', {
    viewModel: function(params){
        var self = this;
        self.parent_id = params.parent_id;
        self.type = params.type;
        self.btnText = params.btnText || '';
        $.extend(self, new PopupBox());
    },
    template: {element: 'posts-detail-popup-template'}
});
