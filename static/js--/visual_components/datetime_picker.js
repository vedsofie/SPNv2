ko.components.register('datetime-picker', {
    viewModel: function(params){
        var self = this;
        self.date = params.$raw.date();
        self.record = params.record;
        self.column = params.column;
        self.isEdit = params.isEdit || false;

        self.bindDateTime = function(element){
            for(var i = 0; i < element.length; i++){
                var el = element[i];
                var $el = $(el);
                if(el.nodeName == "DIV" && $el.datetimepicker){
                    try{
                        var initialValue = $el.data("ko-value");
                        var picker = $el.datetimepicker({
                            defaultDate: initialValue
                        });

                        picker.on("dp.change", function(evt){
                            var newTime = evt.date._d.getTime();
                            self.record[self.column](newTime);
                        });
                    }
                    catch(err){}
                }
            }
        }

        self.currentDate = ko.pureComputed(function(){
            try{
                return self.record[self.column]();
            }
            catch(err){
                return null;
            }
        });

        self.displayDateTime = ko.pureComputed(function(){
            var dt = self.currentDate();
            try{
                return moment(dt).format("MMM Do YYYY [at] h:mma");
            }
            catch(err){
                return null;
            }
        });
    },
    template: {element: 'date-picker'}
});
