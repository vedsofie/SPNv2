function Product(details){
    var self = this;
    $.extend(self, details);

    self.initRecord = function(){
        self.record = new Record(self);
        self.record.addColumn("selectedRunCount", true);
        self.record.addColumn("quantity", true, {isNumber: true});
        self.record.addColumn("Family", false);
        self.record.addColumn("Name", false);
        self.record.addColumn("UnitType__c", false);
        if(typeof self.quantity != "undefined"){
            self.record.quantity(self.quantity);
        }
        else{
            self.record.quantity(1);
        }
    }
    self.initRecord();
    self.label = ko.observable();
    self.price = ko.observable(0);

    self.addOns = ko.computed(function(){
        if(self.AddOnProducts__r){
            var pdts = [];
            for(var i = 0; i < self.AddOnProducts__r['records'].length; i++){
                var addOnPdt = self.AddOnProducts__r['records'][i];
                if(addOnPdt['Product__r']){
                    var pdt = new Product(addOnPdt['Product__r']);
                    pdt.record.quantity(0);
                }
                else{
                    var pdt = new Product(addOnPdt);

                }

                pdts.push(pdt);
            }
            return pdts;
        }
        return [];
    });

    self.breakdown = ko.computed(function(){
        var pdts = [];
        if(self.Breakdown_Products__r){
            if(self.Breakdown_Products__r && self.Breakdown_Products__r['records']){
                for(var i = 0; i < self.Breakdown_Products__r['records'].length; i++){
                    var brkPdt = self.Breakdown_Products__r['records'][i];
                    var breakdownProduct = new Product(brkPdt['Product__r']);
                    breakdownProduct.label(brkPdt['Name'])
                    breakdownProduct.record.quantity(brkPdt['Quantity__c']);
                    pdts.push(breakdownProduct);
                }
            }
            else{
                for(var i = 0; i < self.Breakdown_Products__r.length; i++){
                    var pdt = self.Breakdown_Products__r[i];
                    pdt = new Product(pdt);
                                                            pdts.push(pdt);
                }
            }

        }
        return pdts;
    });

    self.lineItemTotal = ko.pureComputed(function(){
        var products = self.getAllProducts();
        var total = self.price() * self.record.quantity() * 1000 / 1000;
        total = total ? total : 0;
        for(var i = 0; i < products.length; i++){
            var pdt = products[i];
            if(pdt != self){
                total += pdt.lineItemTotal();
            }
        }
        total = total*1000/1000;
        return total;
    });

    self.displayedTotal = ko.pureComputed(function(){
        return self.lineItemTotal().toFixed(2).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    });

    self.getAllProducts = function(){
        var allProducts = [self];
        allProducts = allProducts.concat(self.addOns());
        allProducts = allProducts.concat(self.breakdown());
        return allProducts;
    }

    self.visualTemplate = ko.pureComputed(function(){
        var fam = self.record.Family();
        fam = fam ? fam.replace(' ', '_'): "";
        var templateName = fam + '_template';
        if($('#' + templateName).eq(0).length > 0){
            return templateName;
        }
        return 'products_default_template';
    });
    
    self.unitDisplayText = 'per ' + self.record.UnitType__c()
    
    self.displayUnit = ko.pureComputed(function(){
        return self.record.UnitType__c() + (self.record.quantity() > 1 ? 's' : '');
    });

    self.includedAddons = ko.pureComputed(function(){
        var included = [];
        for(var i = 0; i < self.addOns().length; i++){
            var addOn = self.addOns()[i];
            var quantity = addOn.record.quantity();
            if(quantity > 0){
                included.push(addOn);
            }
        }
        return included;
    });

    self.parentToJSON = self.record.toJSON;
    self.toJSON = function(){
        var json = self.parentToJSON();
        delete json['attributes']
        delete json['Product__r']
        var addOnProducts = JSON.parse(JSON.stringify(self.includedAddons()));
        var breakDownPdts = JSON.parse(JSON.stringify(self.breakdown()));
        delete json['AddOnProducts__r']
        delete json['Breakdown_Products__r']

        json['AddOnProducts__r'] = {'records':  addOnProducts};
        json['Breakdown_Products__r'] = breakDownPdts;
        return json;
    }

    self.unitType = self.record.UnitType__c();
}

function createProducts(sfdcProducts){
    var pdts = [];
    for(var i = 0; i < sfdcProducts.length; i++){
        pdts.push(new Product(sfdcProducts[i]));
    }
    setPricepoints(pdts);
    return pdts;
}

function flattenProducts(pdts){
    var allProducts = [];
    for(var i = 0; i < pdts.length; i++){
        allProducts = allProducts.concat(pdts[i].getAllProducts());
    }
    return allProducts;

}

function pluckIds(sObjects){
    ids = [];
    for(var i = 0; i < sObjects.length; i++){
        obj = sObjects[i];
        ids.push(obj.record.Id());
    }
    return ids;
}

function cloneProduct(pdt){
    var clonedPdt = new Product(pdt.record.toJSON());
    clonedPdt.record.quantity(pdt.record.quantity());
    clonedPdt.price(pdt.price());
    for(var i = 0; i < pdt.addOns().length; i++){
        var addOnOriginal = pdt.addOns()[i];
        clonedPdt.addOns()[i].price(addOnOriginal.price());
        clonedPdt.addOns()[i].record.quantity(addOnOriginal.record.quantity());
        clonedPdt.addOns()[i].label(addOnOriginal.label());
    }

    return clonedPdt;
}



function setPricepoints(pdts){
    var pdts = flattenProducts(pdts);
    var pdtIds = pluckIds(pdts);

    var doSetPricePoints = function(pdts) {
        return function(res, textStatus, jqXHR) {
            for(var i = 0; i < pdts.length; i++){
                var pdt = pdts[i];
                var price = res[pdt.record.Id()];
                pdt.price(price);
            }
        };
    };

    if(window.simulateProducts){
        doSetPricePoints(pdts)(samplePricePoints());
    }
    else{
        $.ajax("/product/price_points", {
                method: "post",
                contentType: "application/json",
                headers: {"Content-Type": "application/json", "Accept": "application/json"},
                data: JSON.stringify(pdtIds)
               })
        .success(doSetPricePoints(pdts));
    }
}
