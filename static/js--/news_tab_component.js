var NewsTabComponent = function(){
    var self = this;

    self.goToTab = ""
    var TabData = function(){
        var self = this;
        self.records = ko.observableArray();
        function FollowingCtrl(rec){
            var self = this;
            self.reference = ko.observable(rec);
            self.record = rec;

            self.reference.subscribe(function(newVal){
                if(newVal){
                    newVal.isExpanded.subscribe(function(isExpanded){
                        if(self.reference().hasNotifications() && isExpanded && self.record.FollowingID){
                            $.ajax("/notification/" + self.record.FollowingID + "/", {method: "DELETE"}).success(function(res){
                                self.reference().hasNotifications(false);
                                self.record.hasNotifications = false;
                                self.hasNotifications(false);
                                self.hasNotifications();
                            }).fail(function(err){
                                console.log(err);
                            });
                        }
                    });
                }
            });
            self.hasNotifications = ko.observable(self.record.hasNotifications);
        }
        self.hasNotifications = ko.pureComputed(function(){
            var recs = self.records();
            for(var i = 0; i < recs.length; i++){
                var post = recs[i];
                if(post.hasNotifications()){
                    return true;
                }
            }
            return false;
        });
        self.addRecord = function(rec){
            var followingCtrl = new FollowingCtrl(rec);
            self.records.push(followingCtrl);
        }

        self.removeRecord = function(recId){
            var records = self.records();
            var newList = [];
            for(var i = 0; i < records.length; i++){
                var record = records[i];
                var followingId = record.record.FollowingID;
                if(recId != followingId){
                    newList.push(record);
                }
            }
            self.records(newList);
        }
    }
    self.followingList = ko.observable({"Sequences": new TabData(),
                                        "Molecules": new TabData(),
                                        "Forums": new TabData(),
                                        "FieldService": new TabData()
                                        });

    self.followingMapping = {"Sequences": Sequence, "Molecules": Molecule, "FieldService": Molecule}

    $.ajax("/user/following/", {cache: false}).success(function(res){
        for(var i = 0; i < res.length; i++){
            var following = res[i];
            following.EmailSubscribed = ko.observable(following.EmailSubscribed);
            following.dt = following.CreatedDate;
            following.dt1 = following.ClosedDate;
            following.CaseNumber = following.CaseNumber ? following.CaseNumber : "Not Assigned ";
            following.CreatedDate = ko.computed(function(){
               return moment(following.dt).format("MM/DD/YYYY [at] h:mma");
            });

            following.ClosedDate = ko.computed(function(){
               var result = moment(following.dt1).format("MM/DD/YYYY [at] h:mma");
               if(result == "Invalid date") { //yet to be closed
                    result = "Not Closed"
               }
               return result
            });
            var type = following.Type;
            if(following.SubType){
                type = following.SubType;
            }
            self.followingList()[type].addRecord(following);
        }
        self.followingList.valueHasMutated();
        
        if(self.selectedTabsFollowing().length == 0){
            self.goToFollowing({"tab": "FieldService"});
        }

        if(self.currentTab == 'dashboard') {
            if(self.goToTab == 'probe') {
                self.goToFollowing({"tab": "Molecules"});
            }else if(self.goToTab == 'sequence') {
                self.goToFollowing({"tab": "Sequences"});
            }else{
                self.goToFollowing({"tab": "Forums"});
            }
        }else{
            self.goToFollowing({"tab": "FieldService"});
        }
        
    }).fail(function(err){
        console.log(err);
    });

    self.currentTab = 'dashboard';
    self.currentSubTab = ko.observable('')

    self.selectTab = function(tab){
        self.selectedTab(tab);
    }

    self.selectedTabsFollowing = ko.pureComputed(function(){
        var tab = self.selectedTab();
        var res = self.followingList()[tab].records();
        return res;
    });

    self.goToFollowing = function(followingId){
        if(followingId){
            var tab = followingId.tab;
            self.selectTab(tab);
            self.currentSubTab(tab)
            if(followingId.following){
                var id = followingId.following;
                setTimeout(function(){
                    $("#following_" + id).goTo();
                }, 500);
            }
        }
    }

    self.close = function(ele){
        var forumID = $(ele).data('forum-id');
        var followingID = $(ele).data('following-id');
        applicationConfirmation.prompt("Are you sure you want to close this issue?", function(confirmed){
            if(confirmed){
                $.ajax("/issue/close/" + forumID).success(function(res){
                    var selectedTab = self.followingList()[self.selectedTab()];
                    selectedTab.removeRecord(followingID);
                }).fail(function(err){
                    console.log(err);
                });
            }
        });
    }

    self.showOpen = ko.observable(true);

    self.doOpen = function(open){
        self.showOpen(open);
    }
    //self.issueCtrl = new ReportIssueCtrl({hideButton: false});

    self.closedIssues = ko.pureComputed(function(){
        return _.orderBy(_.filter(self.selectedTabsFollowing(), function(rec){
            return rec.record.ReadOnly;
        }), function(item){
            return item.record.dt1;
        }, "desc");

    });

    self.openIssues = ko.pureComputed(function(){
        return _.orderBy(_.filter(self.selectedTabsFollowing(), function(rec){
            return !rec.record.ReadOnly;
        }), function(item){
            return item.record.CreatedDate();
        }, "asc");
    });

    self.selectedTab = ko.observable("Sequences");
}