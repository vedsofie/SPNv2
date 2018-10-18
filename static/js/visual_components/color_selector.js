ko.components.register('color-selector', {
    viewModel: function(params){
        var self = this;
        var editable = false;
        if(params.record){
            editable = true;
            self.record = params.record;
            self.column = params.column;
        }
        else{
            self.uneditableColor = params.color;
        }


        self.color = ko.pureComputed(function(){
            if(self.uneditableColor){
                return self.uneditableColor;
            }
            else{
                var color = self.record[self.column]();
                if(!color){
                    self.getRandomColor();
                    color = self.record[self.column]();
                }
                return color.toString();
            }
        });

        self.getRandomColor = function(){
            if(editable){
                var color = goldenColors.getHsvGolden(0.5, 0.95);
                color = color.toHexString();
                self.record[self.column](color);
            }
        }
    },
    template: {element: 'color_selector_template'}
});