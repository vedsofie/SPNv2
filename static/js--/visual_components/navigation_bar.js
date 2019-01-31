var NavigationBar = function(){
    var self = this;
    self.showApplicationSettings = ko.observable(false);
    self.showCreate = ko.observable(false);
    self.currentlyOpenedTab = ko.observable("");
    self.profileCtrl = new UserDetailPopupCtrl({btnText: 'My Profile',
                                                user: runningUser,
                                                hideButton: true,
                                                passwordResetRequired: window.resetPassword});

    self.newUserCtrl = new UserDetailPopupCtrl({AccountID: runningUser.record.AccountID,
                                                hideButton: true});
    self.organizationCtrl = new AccountDetailPopup({hideButton: true});
    //self.issueCtrl = new ReportIssueCtrl({hideButton: true});
    self.sequenceCtrl = new SequenceDetailPopup({hideButton: true,
                                                 idPrefix: 'sequence'});
    self.moleculeCtrl = new MoleculeDetailPopup({hideButton: true,
                                                 idPrefix: 'molecule'});

    self.visit = function(data){
        window.location = data;
    }

    self.toggleSettings = function(){
        var currentState = self.showApplicationSettings();
        self.showApplicationSettings(!currentState);
    }

    self.toggleCreate = function(){
        var currentState = self.showCreate();
        self.showCreate(!currentState);
    }

    self.hideSettings = function(){
        setTimeout(function(){
            self.showApplicationSettings(false);
        }, 300);
        return true;
    }

    self.hideCreate = function(){
        setTimeout(function(){
            self.showCreate(false);
        }, 300);
        return true;
    }

    self.openMyProfile = function(){
        self.profileCtrl.open();
    }

    self.canCreateOrg = ko.pureComputed(function(){
        return runningUser && runningUser.RoleType == "super-admin";
    });

    self.canCreateUser = ko.pureComputed(function(){
        return runningUser && (runningUser.RoleType == "admin" || runningUser.RoleType == "super-admin");
    });

    self.canViewSoftware = function(){
        if(typeof runningUser !== 'undefined'){
            return runningUser.RoleType == 'super-admin';
        }
        return true;
    }

    self.openCreateOrg = function(){
        self.organizationCtrl.open();
    }

    self.openCreateUser = function(){
        self.newUserCtrl.open();
    }

    self.openCreateProbe = function(){
        self.moleculeCtrl.open();
    }

    self.openNewSynth = function(){
        self.sequenceCtrl.open();
    }

    self.openReportIssue = function(){
        self.issueCtrl.open();
    }
}
