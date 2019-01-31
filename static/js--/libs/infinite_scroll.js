// knockout-js-infinite-scroll (common usage)
InfiniteScroll = function(records) {
    var self = this;
    self.items = ko.observableArray();
    self.items.extend({
        infinitescroll: {}
    });

    // detect resize
    $(window).resize(function() {
        updateViewportDimensions();
    });

    self.fetchMore = function(numTotal){
        console.log("here is our pagination method");
    }

    self.init = function(records){
        var newItems = [];
        for(var i = 0; i < records.length; i++){
            newItems.push(records[i]);
        }

        self.items(newItems);
    }
    records.subscribe(function(newVal){
        self.init(newVal);
    });
    self.init(records());

    // update dimensions of infinite-scroll viewport and item
    function updateViewportDimensions() {
        var itemsRef = $('#itemsUL'),
            itemRef = $('.item').first(),
            itemsWidth = 1,//itemsRef.width(),
            itemsHeight = 550,//itemsRef.height(),
            itemWidth = 1,//itemRef.width(),
            itemHeight = 70;//itemRef.height();

        self.items.infinitescroll.viewportWidth(itemsWidth);
        self.items.infinitescroll.viewportHeight(itemsHeight);
        self.items.infinitescroll.itemWidth(itemWidth);
        self.items.infinitescroll.itemHeight(itemHeight);

    }

    function bindScroll(){
        $('#itemsUL').scroll(_.debounce(function() {
           self.items.infinitescroll.scrollY($('#itemsUL').scrollTop());
            // add more items if scroll reaches the last 100 items
            if (self.items.peek().length - self.items.infinitescroll.lastVisibleIndex.peek() <= 1) {
                self.fetchMore();
            }
        }, 250));
    }

    self.bindDom = function(){
        bindScroll()
        updateViewportDimensions();
    }
}