function User(details){
    var self = this;
    $.extend(self, details);

    self.initRecord = function(){
        self.record = new Record(self);
        self.record.addColumn("UserID", false);

        self.canEditRole = function(){
            if(!runningUser){
                return false;
            }
            var canEdit = runningUser.UserID != self.UserID && runningUser.RoleType != 'standard user';
            canEdit &= !(self.RoleType == 'super-admin' && runningUser.RoleType == 'admin');
            return canEdit;
        }

        var canEditUserName = self.record.UserID() == null;

        self.canEditPassword = function(){
            return runningUser.UserID == self.UserID;
        }

        self.record.addColumn("RoleID", self.canEditRole, {presence: true, isNumber: true});
        self.record.addColumn("avatar");
        self.record.addColumn("username", canEditUserName, {presence: true,length: {maximum: 80}});
        self.record.addColumn("FirstName", true, {presence: true,length: {maximum: 100}});
        self.record.addColumn("LastName", true, {presence: true,length: {maximum: 100}});
        self.record.addColumn("Email", true, {presence: true, email: true,length: {maximum: 100}});
        self.record.addColumn("title", true, {length: {maximum: 100}});
        self.record.addColumn("password", self.canEditPassword, {length: 8});
        self.record.addColumn("Phone", true, {length: {maximum: 20}});
    }
    self.initRecord(self);
    self.account = ko.observable(new Account({"name":""}));
    self.sequences = ko.observableArray();
    self.isPrimaryContact = ko.observable(false);
    self.Role = ko.observable();

    self.canEdit = function(){
        return runningUser.RoleType == 'super-admin' ||
               runningUser.RoleType=='admin' && runningUser.AccountID == self.AccountID ||
               runningUser.UserID == self.UserID;
    }

    self.calculatedRole = ko.pureComputed(function(){
        if(self.Role()){
            console.log('defined');
            return self.Role();
        }
        else{
            $.ajax("/user/" + self.record.UserID() + "/role/", {cached: false}).success(function(res){
                console.log(res);
                self.Role(res);
            }).fail(function(err){
                console.log(err);
            });
        }
        return self.Role();
    });

    self.calculated_account = ko.pureComputed(function(){
        $.ajax("/account/" + self.AccountID + "/", {
            method: "get",
            cache: false,
            headers: {"Accept": "application/json"},
            success: function(res){
                self.account(res);
            }
        });
        return self.account;
    });

    self.calculated_sequences = ko.pureComputed(function(){
        $.ajax("/user/" + self.getUserID() + "/sequences", {
            method: "get",
            headers: {"Accept": "application/json"},
            success: function(res){
                res = JSON.parse(res);
                self.sequences(initSequences(res));
            }
        });
        return self.sequences;
    });

    self.getUserID = ko.computed(function(){
        return self.userid || self.UserID;
    });

    self.name = ko.pureComputed(function(){
        var firstname = self.firstname || self.FirstName || "";
        var lastname = self.lastname || self.LastName || "";
        if(firstname && lastname){
            return firstname + " " + lastname;
        }
        else if(self.getUserID){
            return self.userid || self.record.UserID();
        }
        return "";
    });

    self.save = function(){
        return self.record.save("/user/create").success(function(res){
            if(res.UserID){
                self.record.UserID(res.UserID);
                self.record.UserID.valueHasMutated();
            }
        });
    }

    self.roles = ko.observableArray();
    self.calculatingRoles = ko.observable(false);
    self.computedRoles = ko.pureComputed(function(){
        if(self.roles().length == 0 && !self.calculatingRoles()){
            self.calculatingRoles(true);
            $.ajax("/account/" + self.AccountID + "/user/available_roles/").success(function(res){
                self.roles(res);
                self.calculatingRoles(false);
            }).fail(function(err){
                console.log(err);
            });
        }
        return self.roles();
    });
}