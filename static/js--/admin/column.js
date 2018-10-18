var Column = function(data){
    var self = this;
    $.extend(self, data);
    self.getType = function(){

        if(self.type.startsWith('VARCHAR')){
            var x = self.type;
            x = x.slice(8, x.length-1);
            try{
                x = parseInt(x);
                if(x > 100){
                    return 'textarea';
                }
            }
            catch(err){}
            return 'text';
        }
        else if(self.type == "TEXT"){
            return 'textarea';
        }
        else if(self.type == "BYTEA"){
            return "BLOB"
        }
        else if(self.type == 'TIMESTAMP WITHOUT TIME ZONE'){
            return 'DATETIME';
        }
        else if(self.references){
            return 'lookup';
        }
        else if(self.type =='BOOLEAN'){
            return 'BOOLEAN';
        }
        console.log(self.type);
        return self.type;
    }

    self.typeIsKnown = function(){
        var types = ["text", "DATETIME", 'lookup', "PolymorphicLookup", "BLOB", 'textarea', "RandomColor", 'INTEGER', "SFDC", 'BOOLEAN'];
        return types.includes(self.getType());
    }
}