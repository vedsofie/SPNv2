var Picklist = function(options){
    var self = this;
    options = options || {};
    self.options = options['options'];
    self.optionsPrimaryText = options['optionsPrimaryText'];
    self.optionsText = options['optionsText'];
    self.optionsUnitType = options['optionsUnitType'];
    self.value = options['value'];
    
    self.showCreate = ko.observable(false);

    self.toggleCreate = function(){
        var currentState = self.showCreate();
        self.showCreate(!currentState);
    }

    self.hideCreate = function(){
        setTimeout(function(){
            self.showCreate(false);
        }, 300);
        return true;
    }

    self.onSelect = function(value){
        self.value(value);
    }

    self.selectedOptionText = ko.pureComputed(function(){
        if(self.value()){
            return "per " + self.value()[self.optionsUnitType];
        }
        return "";
    });

    self.selectedOptionPrimaryText = ko.pureComputed(function(){
        if(self.value()){
            return self.value()[self.optionsPrimaryText];
        }
        return "";
    });
    

    self.sortedOptions = ko.computed(function(){
        return _.orderBy(self.options(), function(item){
            return item.price();
        });
    });
}

ko.components.register('picklist', {
    viewModel: function(params){
        return new Picklist(params)
    },
    template: {element: 'picklist-template'}
});
