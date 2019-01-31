var uniqueIdentifier = 0;
function Keyword(details){
    var self = this;
    $.extend(self, details);
    self.initRecord = function(){
        self.record = new Record(self);
        self.record.addColumn("KeywordID");
        self.record.addColumn("Keyword");
        self.record.addColumn("ParentID");
        self.record.addColumn("Type");
        self.record.addColumn("CreationDate");
        self.record.addColumn("ClosedDate");
        self.record.addColumn("Category");
        self.record.addColumn("DisplayFormat");
    }
    self.useFormulaEditor = details.useFormulaEditor || false;
    self.htmlID = 'keyword_element_' + uniqueIdentifier;
    uniqueIdentifier++;
    self.initRecord(self);
    self.index = ko.observable();
    self.canEdit = ko.pureComputed(function(){
        var hasIndex = self.index();
        var isNew = !self.record.KeywordID();
        return !hasIndex && isNew;
    });
    self.canDelete = ko.pureComputed(function(){
        return self.record.KeywordID() != null || self.index();
    });

}