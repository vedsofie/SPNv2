function TimerInput(params) {
    var self = this;
    self.edit = params.edit || false;
    var target = params.value;
    var initial = parseInt(target() || 0);
    var min = params.min || 0;
    var max = params.max || 3599; // 59:59
    if( params.enable ) {
        self.enable = params.enable;
    }
    else {
        self.enable = true;
    }

    var secondObs = ko.observable(initial % 60);
    self.second = ko.computed({
        read: function() {
            var value = parseInt(target()) % 60;
            if( value < 10 ) {
              return "0" + value;
            }
            else {
              return value;
            }
        },
        write: function(value) {
            secondObs(isNaN(value) ? 0 : value);
        }
    });

    var minuteObs = ko.observable(parseInt(initial / 60));
    self.minute = ko.computed({
        read: function() {
            var value = parseInt(target() / 60);
            if( value < 10 ) {
              return "0" + value;
            }
            else {
              return value;
            }
        },
        write: function(value) {
            minuteObs(isNaN(value) ? 0 : value);
        }
    });

    var time = ko.pureComputed(function() {
        var minute = parseInt(minuteObs());
        var second = parseInt(secondObs());
        return (isNaN(minute) ? 0 : minute * 60) + (isNaN(second) ? 0 : second);
    });

    time.subscribe(function(newValue) {
        target(newValue);
    });

    self.canIncrement = ko.pureComputed(function() {
        return ko.unwrap(self.enable) && target() < ko.unwrap(max);
    });

    self.increment = function() {
        var newValue = target() + 1;
        target(newValue);
    }

    self.canDecrement = ko.pureComputed(function() {
        return ko.unwrap(self.enable) && target() > ko.unwrap(min);
    });

    self.decrement = function() {
        var newValue = target() - 1;
        target(newValue);
    };

    self.dispose = function() {
        self.second.dispose();
        self.minute.dispose();
    }
}

ko.components.register('timer-input', {
    viewModel: function(params){
        return new TimerInput(params)
    },
    template: {element: 'timer-input-template'}
});