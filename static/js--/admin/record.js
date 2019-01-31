var Record = function(data){
    var self = this;
    self.columns = [];
    self.errors = {};
    self.edit = {};
    self.constraints = {};
    self.isSaving = ko.observable(false);

    self.getValue = function(col){
        if(self[col]){
            return self[col]();
        }
        else{
            return null;
        }
    }

    self.toJSON = function(){
        var map = {}
        for(var i = 0; i < self.columns.length; i++){
            var col = self.columns[i];
            var value = self[col]();
            if(self.columnIsNumber(col)){
                if(typeof value === 'undefined' || value == "" || value == null){
                    if(self.columnRequired(col)){
                        // do not include it in the map let it fail
                    }
                    else{
                        map[col] = null;
                    }
                }
                else{
                    map[col] = value;
                }
            }
            else{
                map[col] = value;
            }
        }
        return map;
    }

    self.addColumn = function(col, canEdit, constraints){
        if(typeof canEdit === 'undefined'){
            canEdit = true;
        }
        if(typeof constraints === 'undefined'){
            constraints = {};
        }
        if(!self[col]){
            self[col] = ko.observable();
            self.columns.push(col);
            self[col].subscribe(function(newVal){
                self.isDirty(true);
            });
        }
        self.errors[col] = ko.observable();
        self.edit[col] = canEdit;
        self.constraints[col] = constraints;
    }

    self.valid = function(){
        self.clearErrors();
        resp = validate(self.toJSON(), self.constraints);
        if(resp){
            for(errCol in resp){
                var firstError = resp[errCol][0]
                self.addError({field: errCol, message: firstError});
            }
            return false;
        }
        return true;
    }

    self.canEdit = function(col){
        var res = self.edit[col];
        if(typeof res === 'function'){
            return res();
        }
        return self.edit[col];
    }

    self.columnRequired = function(col){
        if(self.constraints[col]){
            var colContraints = self.constraints[col];
            var presence = colContraints.presence;
            return typeof presence !== 'undefined';
        }
        return false;
    }

    self.columnIsNumber = function(col){
        if(self.constraints[col]){
            var colContraints = self.constraints[col];
            var presence = colContraints.isNumber;
            return typeof presence !== 'undefined';
        }
        return false;
    }

    self.clearErrors = function(){
        for(var col in self.errors){
            self.errors[col]("");
        }
    }

    self.addError = function(err){
        self.errors[err.field](err.message);
        self.errors[err.field].valueHasMutated();
    }

    self.isDirty = ko.observable(false);

    self.revert = function(rec){
        for(var i = 0; i < self.columns.length; i++){
            var col = self.columns[i];
            var oldVal = rec[col];
            self[col](oldVal);
        }
        self.clearErrors();
    }

    self.cleanseData = function(){
        for(columnName in self.columns){
            columnName = self.columns[columnName];
            var constraints = self.constraints[columnName];
            var colValue = self[columnName]();
            if(constraints){
                if(constraints.isNumber){
                    self[columnName](parseFloat(colValue));
                }
                else if(constraints.isInteger){
                    self[columnName](parseInt(colValue));
                }
            }

        }
    }

    self.save = function(saveUrl){
        self.clearErrors();
        self.cleanseData();
        var rec = JSON.stringify(self);
        self.isSaving(true);
        console.log("Save")
        console.log(saveUrl)
        return $.ajax(saveUrl, {
                                method: "post",
                                contentType: "application/json",
                                headers: {"Content-Type": "application/json", "Accept": "application/json"},
                                data: rec
                               }
        ).success(function(res){
            self.isSaving(false);
        }).fail(self.handleFailures);
    }

    self.saveForm = function(saveUrl, values){
        var formData = new FormData();
        for(key in values){
            formData.append(key, values[key])
        }
        self.isSaving(true);

        return $.ajax(saveUrl, {
            method: 'post',
            processData: false,
            contentType: false,
            data: formData
        }).success(function(res){
            self.isSaving(false);
        }).fail(self.handleFailures);
    }

    self.handleFailures = function(err){
        self.isSaving(false);
        if(err.responseJSON){
            var json = err.responseJSON;
            var errDetails = json['error_details'];
            if(typeof errDetails == "object"){
                for(var i = 0; i < errDetails.length; i++){
                    var err = errDetails[i];
                    self.addError(err);
                }
            }
            else{
                alert('An unknown error has occured.  Please contact SofieBio if the error persists');
            }
        }
        else{
            if(err.responseText){
                alert(err.responseText);
            }
            else{
                alert('An unknown error has occured.  Please contact SofieBio if the error persists');
            }
        }
    }

    for(var col in data){
        self.addColumn(col);
        self[col](data[col]);
    }
}