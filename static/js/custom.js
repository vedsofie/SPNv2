$(document).ready(function(){
// Some common functions
var back_button_visible = false;
// Function to change the current url with site or probe search parameters
function urlChanger(site = "",probe ="" ){
    currentUrl = window.location.href;
    currentUrl = currentUrl.split('?')[0]; // get only the url without parameters - useful for repeat requests
    newUrl = currentUrl + "?site=" + site + "&probe=" +  probe;
    return newUrl;
}

// Initialization functions for maps page

// Check if URL has get parameters for search, and if exists, change what is displayed. This is useful when the page first loads, or reloads. 

    // Check if url has parameters
    has_params = (window.location.href).includes("?site");
    if (has_params) {
        // code to change the UI below search bar
    }
    else{
        $("span.input-btn-left").hide();
    }


// When back button is clicked, check url for parameters and hide the back button when no parameters are found

// Function to be called when adding parameters to the URL

function searchEventChanges(){
    if (back_button_visible) {
         
    }
    else{
       $("span.input-btn-left").show('slide', {direction: 'left'}, 1000);
       $("div.probe-default-headline").hide('fade', 500);
    }
}
// ========== Drop down autocomplete logic =============
  var results = [{ 
        value: "[18 F] Fallypride",
        probe_label: "[18 F] Fallypride",
        result_type: "Probe",
        icon_path: "",
        probe_count: ""
    }, { 
        value: "FMISO",
        probe_label: "FMISO-SOFIE",
        result_type: "Probe",
        icon_path: "",
        probe_count: ""
    }
    ,{
        value: "UCLA Crump Institute",
        probe_label: "UCLA Crump Institute",
        result_type: "Site",
        icon_path: "",
        probe_count: ""
    }];
  $("#probe-search").autocomplete({
        minLength: 0,
        source: results,
        focus: function (event, ui) {
            $("#probe-search").val(ui.item.probe_label);
            return false;
        },
        select: function (event, ui) {
            $("#probe-search").val(ui.item.probe_label);
            probe_search_val = $("#probe-search").val();
            // alert(probe_search_val);
            if (ui.item.result_type == "Probe") {
                window.history.pushState(null, null, urlChanger("",probe_search_val));
                searchEventChanges();
                back_button_visible = true;
            }
            else{
                window.history.pushState(null, null, urlChanger(probe_search_val,""));
                searchEventChanges();
                back_button_visible = true;
            }
        }
    }).data("ui-autocomplete")._renderItem = function (ul, item) {
        return $("<li>")
            .data("ui-autocomplete-item", item)
            .append('<div class="probe-results-div"><a> <h6 class="text-left">'+ item.probe_label +'</h6> <br /> <button class="btn btn-primary btn-xs">'+ item.result_type+ '</button>'+ "</a></div>")
            .appendTo(ul)
        };

//  ======== End of autocomplete logic ============

});
