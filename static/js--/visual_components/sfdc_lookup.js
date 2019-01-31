var SFDCLookup = function(params){
    var self = this;
    self.record = params.record;
    self.col = params.col;

    self.salesforceObject = self.col.field_info.sObjectType;
    self.queryFields = self.col.field_info.QueryFields || "Name";
    self.filterField = self.col.field_info.FilterField || "Name";
    self.queriedFields = self.queryFields.split(",");

    var myParams = {
                    'sObjectType': 'SFDC',
                    'record': self.record,
                    'column': self.col.name,
                    'displayLink': true
    };
    var lookup = new Lookup(myParams);
    lookup.calculatedName = ko.computed(function(){
        return self.record[self.col.name];
    });

    $.extend(self, lookup);

    self.doSearch = function(txt){
        var filter = self.searchTxt();
        var searchText = "Select Id," + self.queryFields + " from " + self.salesforceObject;
        searchText += " where " + self.filterField + " like '%" + filter + "%'";
        var url = "/admin/sfdc/search/" + searchText + "/";
        $.ajax(url).success(function(res){

            var results = [];
            for(var i = 0; i < res.length; i++){
                var re = res[i];

                re['id'] = re.Id;
                re['name'] = re[self.queriedFields[0]];
                results.push(re);

            }
            self.searchResults(results);
            //self.searchResults(res);
        });
    }
}

ko.components.register('sfdc-lookup', {
    viewModel: function(params){
        return new SFDCLookup(params);
    },
    template: {element: 'sfdc-lookup-template'}
});