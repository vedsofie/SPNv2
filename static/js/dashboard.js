var PopularDownloads = function(){
    var self = this;
    self.popularList = ko.observableArray();
    self.newSequences = ko.observableArray();
    $.ajax("/sequence/most_popular", {cache: false}).success(function(res){
        var lst = []
        for(var i = 0; i < res.length; i++){
            var popSeq = new Sequence(res[i].obj);
            popSeq.numdownloads = res[i].numdownloads;
            lst.push(popSeq);
        }
        self.popularList(lst);
    }).fail(function(err){
        console.log(err);
    });
    self.hasPopularDownloads = ko.pureComputed(function(){
        return self.popularList().length > 0;
    });
    self.hasMostNewSequences = ko.pureComputed(function(){
        return self.newSequences().length > 0;
    });
    $.ajax("/sequence/most_new", {cache: false}).success(function(res){
        self.newSequences(res);
    }).fail(function(err){
        console.log(err);
    });

    self.displayDateTime = function(dt){
        try{
            return moment(dt).format("MMM Do YYYY [at] h:mma");
        }
        catch(err){
            return null;
        }
    }
}