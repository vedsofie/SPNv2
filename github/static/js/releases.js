function ReleaseIssue(release_name){
    var self = this;
    self.release = release_name;
    self.title = ko.observable("");
    self.message = ko.observable("");

    this.report = function(){
        console.log("Reporting...");
        $.ajax("/github/report/issue", {
            method: "post",
            data: {
                "release": self.release,
                "title": self.title(),
                "message" : self.message()
            }
        }).success(function(res){
            console.log(res);
        }).fail(function(err){
            console.log(err);
        });
    }
}

function Release(details){
    var self = this;
    self.showReleases = ko.observable(false);
    self.showComments = ko.observable(false);
    self.reportingIssue = ko.observable(false);
    self.comments = ko.observableArray();
    $.extend(self, details);

    self.newIssue = ko.observable(new ReleaseIssue(self.name));
    self.canDownload = ko.pureComputed(function(){
        if(self.versions.length > 0){
            return true;
        }
        return false;
    });

    self.download = function(asset_url){
        self.hideVersions();
        var url = "/github/download/asset?url=" + encodeURIComponent(asset_url);
        window.location = url;
    }

    self.promptVersionToDownload = function(){
        self.showReleases(true);
    }

    self.hideVersions = function(){
        self.showReleases(false);
    }

    self.toggleViewComments = function(){
        self.showComments(!self.showComments());
    }

    self.calculatedComments = ko.pureComputed(function(){
        $.ajax("/github/release/" + self.name + "/comments").success(function(res){
            self.comments(res);
            if(self.comments().length == 0){
                self.commentsMessage("No Comments");
            }
            else{
                self.commentsMessage("");
            }
        }).fail(function(err){
            console.log(err);
        });
        return self.comments;
    });

    self.createIssue = function(){
        self.reportingIssue(true);
    }

    self.reportIssue = function(){
        self.newIssue().report();
        self.newIssue(new ReleaseIssue(self.name));
        self.reportingIssue(false);
    }

    self.cancelReport = function(){
        self.newIssue(new ReleaseIssue(self.name));
        self.reportingIssue(false);
    }

    self.commentsMessage = ko.observable("Loading Comments. Please Wait...");
}

function initReleases(data){
    var isSoftware = false
    var objs = []
    for( var i=0; i < data.length; i++ ){
        var obj = data[i];
        obj = new Release(obj);
        objs.push(obj)
    }
    return objs;
}





