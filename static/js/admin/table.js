var Table = function(data, name){
    var self = this;
    self.columns = ko.observableArray();
    var list = [];
    if(name == "user") {
        list = ["FirstName", "LastName", "username", "SFDC_ID", "AccountID", "Email", "RoleID"]
    }else if(name == "Account") {
        list = ["name","LabName","PrincipalInvestigatorID", "primary_contact_id", "description", "SFDC_ID", "Latitude", "Longitude", "Address", "City", "State", "ZipCode"]
    }else if(name == "Sequences") {
        list = ["Name", "MoleculeID", "UserID", "CreationDate", "Comment", "MadeOnElixys", "PurificationMethod"] 
    }else if(name == "Molecules") {
        list = ["Name", "Isotope", "UserID", "Approved", "Description", "DisplayFormat", "CAS"]
    }
    if(list.length == 0) {
        for(var i = 0; i < data.length; i++){
            var col = data[i];
            self.columns().push(new Column(col));
        }
    }else{
        for(var i = 0; i < data.length; i++){
            var isAdded = false;
            for(var j = 0; j < list.length; j++) {
                if(data[i].name == list[j]) {
                    list[j] = data[i];
                    isAdded = true;
                    break;
                }
            }
            if(!isAdded) {
                list.push(data[i])
            }
        }
        for(var i = 0; i < list.length; i++) {
            var col = list[i];
            self.columns().push(new Column(col));   
        }
    }

    /*
    self.columns().sort(function(x, y){
        if(x.primary_key){
            return -1;
        }
        else if(y.primary_key){
            return 1;
        }
        return 0;
    });
    */
}