function NumericInput(params) {
    var self = this;
    self.value = params.value;
    self.max = params.max || 9999;
    self.min = params.min || 0;
    self.maxlength = params.maxlength || 3;
    self.step = params.step || 1;
    self.fixed = params.fixed;
    self.input = ko.observable(self.value());
    self.displayUnit = params.displayUnit ? params.displayUnit : '';

    self.input.subscribe(function(newValue) {
        if( !isNaN(newValue) ) {
            self.value(parseFloat(newValue));
        }
    });

    self.canIncrement = ko.pureComputed(function() {
        return ko.unwrap(self.enable) && self.value() < ko.unwrap(self.max);
    });

    self.increment = function() {
        if(self.canIncrement()){
            var newValue = self.value() + self.step;
            if( self.fixed ){
                newValue = newValue.toFixed(self.fixed);
            }
            self.value(newValue);
            self.input(newValue);
        }
    };

    self.canDecrement = ko.pureComputed(function() {
        return ko.unwrap(self.enable) && self.value() > ko.unwrap(self.min);
    });

    self.decrement = function() {
        if(self.canDecrement()){
            var newValue = self.value() - self.step;
            if( self.fixed ){
                newValue = newValue.toFixed(self.fixed);
            }
            self.value(newValue);
            self.input(newValue);
        }
    }

    if( params.enable ) {
        self.enable = params.enable;
    }
    else {
        self.enable = true;
    }
}

ko.components.register('numeric-input', {
    viewModel: function(params){
        return new NumericInput(params)
    },
    template: {element: 'numeric-input-template'}
});

