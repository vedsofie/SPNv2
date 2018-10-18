var Cart = function(availableProducts, existingProducts){
    var self = this;
    self.initRecord = function(){
        self.record = new Record(self);
    }
    self.initRecord();
    self.products = ko.observableArray();
    self.displayPage = ko.observable();
    self.availableProducts = availableProducts || ko.observableArray();

    $.get("/product/cart/").success(function(res){
        var pdts = createProducts(res);
        for(var i = 0; i < pdts.length; i++){
            var pdt = new Product(pdts[i]);
            self.addProduct(pdt);
        }
        setPricepoints(self.products());


        var availPdts = self.mappedReverseProducts();
        var allPdts = flattenProducts(pdts);
        for(var i = 0; i < allPdts.length; i++){
            var pdt = allPdts[i];
            var availPdt = availPdts[pdt.Id];
            if(typeof availPdt !== "undefined"){
                availPdt.record.quantity(pdt.record.quantity());
            }
        }

    }).fail(function(err){
        console.log("Failed to load products");
    });

    self.addProduct = function(pdt){
        if(typeof self.mappedProducts()[pdt.Id] === 'undefined'){
            var clone = cloneProduct(pdt);
            self.products.push(clone);
        }
        else{
            var clone = cloneProduct(pdt);
            var index = self.mappedProducts()[pdt.Id];

            self.products()[index] = clone;
            self.products.valueHasMutated();
        }

        $.ajax("/product/set_cart/", {
                                method: "post",
                                contentType: "application/json",
                                headers: {"Content-Type": "application/json", "Accept": "application/json"},
                                data: JSON.stringify(JSON.stringify(self.products()))
                               }
        ).success(function(res){
            //self.isSaving(false);
        });
    }



    self.clearCart = function(){
        applicationConfirmation.prompt("Are you sure you want to empty your cart?", function(doClear){
            if(doClear){
                window.location = "/product/clear_cart/";
            }
        });
    }

    self.familySelectors = ko.pureComputed(function(){
        var productsByFamily = {};
        for(var i = 0; i < self.availableProducts().length; i++){
            var family = self.availableProducts()[i].record.Family();
            if(!productsByFamily[family]){
                productsByFamily[family] = [];
            }
            productsByFamily[family].push(self.availableProducts()[i]);
        }

        var families = Object.keys(productsByFamily);
        var resp = [];
        for(var i = 0; i < families.length; i++){
            var pdts = productsByFamily[families[i]];
            var selector = new ProductFamilySelector(pdts);
            resp.push(selector);
        }
        return resp;
    });

    self.mappedProducts = ko.pureComputed(function(){
        var map = {};
        for(var i = 0; i < self.products().length; i++){
            var pdt = self.products()[i];
            map[pdt.Id] = i;
        }
        return map;
    });

    self.mappedReverseProducts = ko.pureComputed(function(){
        var map = {};
        var allPdts = self.availableProducts();
        allPdts = flattenProducts(allPdts);
        for(var i = 0; i < allPdts.length; i++){
            var pdt = allPdts[i];
            map[pdt.Id] = pdt;
        }
        return map;
    });

    self.total = ko.pureComputed(function(){
        var tot = 0;
        for(var i = 0; i < self.products().length; i++){
            tot = tot + self.products()[i].lineItemTotal();
        }
        return tot;
    });

    self.displayedTotal = ko.pureComputed(function(){
        return self.total().toFixed(2).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    });

    self.getAvailableProducts = function(){
        $.get('/product/products').success(function(res){
            self.availableProducts(createProducts(res));
        }).fail(function(err){
            console.log(err);
        });
    }

    self.viewCart = function(){
        self.displayPage("cart-template");
    }

    self.viewProducts = function(){
        self.displayPage("product-list-template");
    }

    self.placeOrder = function(){
        var lineItems = []
        var products = flattenProducts(self.products());
        for(var i = 0; i < products.length; i++){
            var lineItem = {
                "Id": products[i].Id,
                "Quantity": products[i].record.quantity()
            };
            lineItems.push(lineItem);
        }
        var product_ids = pluckIds(products);
        self.record.isSaving(true);

        $.ajax("/product/place_order", {
                method: "post",
                contentType: "application/json",
                headers: {"Content-Type": "application/json", "Accept": "application/json"},
                data: JSON.stringify(lineItems)
               })
        .success(function(res){
            self.record.isSaving(false);
            window.location = "/product/clear_cart/";
        }).fail(function(err){
            self.record.isSaving(false);
        });
    }

    self.viewProducts();


}

var ProductFamilySelector = function(products){
    var self = this;
    self.products = products;
    self.productFamily = self.products[0].record.Family();
    self.productOptions = ko.computed(function(){
        var pdtNames = [];
        for(var i = 0; i < self.products.length; i++){
            var pdt = self.products[i];
            pdtNames.push(pdt);
        }
        return pdtNames;
    });

    var orderedProducts = _.orderBy(self.products, function(item){
        return item.price();
    });

    self.selectedProduct = ko.observable(orderedProducts[0]);

}