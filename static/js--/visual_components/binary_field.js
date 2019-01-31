var binaryUniqueIdentifier = 0;
function BinaryField(params){
        var self = this;
        self.identifier = params.id || binaryUniqueIdentifier;
        binaryUniqueIdentifier++;
        self.record = params.record;
        self.column = params.column;
        self.column_file_name = params.column_file_name;
        self.showClose = typeof params.showClose == 'undefined' ? false : params.showClose;
        self.styledButton = params.styledButton || false;
        self.cropperApplyText = params.cropperApplyText || "Done";
        self.acceptedTypes = params.acceptedTypes || ".jpg,.jpeg,.png,.bmp";
        self.imageDataURL = ko.observable();
        self.showCrop = ko.observable(false);
        self.showImage = params.showImage || false;
        if("aspectRatio" in params){
            self.aspectRatio = params.aspectRatio;
        }
        else{
            self.aspectRatio = 1;
        }
        self.doCrop = params.doCrop;
        self.showCropButton = typeof params.showCropButton === 'undefined' ? true : params.showCropButton;
        self.skipTrigger = false;
        self.edit = params.edit || ko.observable(true);
        self.maxCropWidth = params.maxCropWidth;
        self.maxCropHeight = params.maxCropHeight
        self.uploadText = params.uploadText || "Click here to upload a new image";
        self.cropperApplyResponse = params.cropperApplyResponse;
        if(typeof self.edit !== 'function'){
            self.edit = ko.observable(self.edit);
        }
        var url = params.url;

        self.uploadImage = function(file_name){
            var file_reader = new FileReader();
            file_reader.onload = function(e) {
                var bin = file_reader.result;
                /*
                if(self.imageCropper){
                    console.log("resetting the croppe");
                    self.imageCropper.cropper('reset').cropper('replace', bin);
                }
                */
                self.setImage(bin);
                self.cropImage();
                var img = new Image();
                img.src = self.imageDataURL();
                var imageHeight = img.height;
                var imageWidth = img.width;
                var containerHeight = self.$image.parent().height();
                var containerWidth = self.$image.parent().width();

                var imageHeightStartPt = 0;
                var imageWidthStartPt = 0;
                self.imageCropper.cropper('moveTo', imageWidthStartPt, imageHeightStartPt);
            }
            if(self.column_file_name){
                self.record[self.column_file_name](file_name.name);
            }
            file_reader.readAsDataURL(file_name);
        }

        self.record[self.column].subscribe(function(url){
            if(!self.skipTrigger){
                if(url == null){
                    if(self.originalImage){
                        url = self.originalImage;
                    }
                }
                self.setImage(url);
                self.imageCropper.cropper('reset').cropper('replace', self.imageDataURL());
                setTimeout(function(){
                    var canvas = self.imageCropper.cropper('getCroppedCanvas');
                    self.setImage(canvas.toDataURL());
                }, 4000);

            }
        });

        self.setImage = function(dataURL){
            self.displayImage(false);
            self.imageDataURL(dataURL);
            if(dataURL){
                var binImage = dataURL.substring(dataURL.indexOf(",")+1, dataURL.length);
                self.skipTrigger = true;
                self.record[self.column](binImage);
                self.skipTrigger = false;
            }
        }
        self.displayImage = ko.observable(false);

        self.initCropImage = function(ele){
            if(ele){
                self.$image = $(ele[1]).find('.canvas-image').eq(0);
            }
            var container = self.$image.parent();

            var options = {
                preview: '.img-preview',
                minContainerWidth: container.width(),
                minContainerHeight: container.height(),
                crop: function (e) {
                    self.displayImage(true);
                }
            };
            if(self.aspectRatio){
                options['aspectRatio'] = self.aspectRatio;
            }

            self.imageCropper = self.$image.cropper(options);
            self.imageCropper.cropper('reset').cropper('replace', self.imageDataURL());
        }

        self.cropImage = function(){
            if( self.doCrop ){
                self.showCrop(!self.showCrop());
                if(!self.showCrop()){
                    var canvas = self.imageCropper.cropper('getCroppedCanvas');
                    self.setImage(canvas.toDataURL());
                    if(self.cropperApplyResponse){
                        self.cropperApplyResponse();
                    }
                }

                if(self.imageCropper){
                    self.imageCropper.cropper("destroy");
                    self.initCropImage();
                }
                self.initCropImage();
            }
        }

        self.closeCropWindow = function(){
            self.showCrop(!self.showCrop());
        }

        self.stopMoving = function(){
            clearInterval(self.movingImageTimer);
            self.movingImageTimer = null;
        }

        self.moveImage = function(xOff, yOff){
            self.imageCropper.cropper("move", xOff, yOff);
            if(self.movingImageTimer){
                self.stopMoving();
            }
            else{
                self.movingImageTimer = setInterval(function(){
                    self.imageCropper.cropper("move", xOff, yOff);
                }, 125);
            }
        }

        self.zoomImage = function(ratio){
            self.imageCropper.cropper("zoom", ratio);
        }

        self.originalImage = null;
        if(url){
            self.originalImage = url;
            self.imageDataURL(url);
        }

}


ko.components.register('binary-field', {
    viewModel: function(params){return new BinaryField(params);},
    template: {element: 'binary-image-template'}
});