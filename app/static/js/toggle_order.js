function toggle_select(suo,audit_id) {

    var entry = {
        'suo': suo,
        'audit_id': audit_id
    };
    
    fetch(`${url_for_toggle_order}`, {  // use global var defined in base.html
        method: "POST",
        credentials: "include",
        body: JSON.stringify(entry),
        cache: "no-cache",
        headers: new Headers({"content-type": "application/json"})
    })
    .then(function (response) {
        console.log(response);
        if (response.status !== 200) {
            console.log(`Looks like there was a problem. Status code: ${response.status}`);
            return;
        }
        response.text().then(function (data) {
            data_json = JSON.parse(data);
            if (data_json.selected_for_audit) {
                $("#glyph_" + suo).removeClass();
                $("#glyph_" + suo).addClass("glyphicon glyphicon-ok-circle"); // only one of these should be present at once
            } else {
            $("#glyph_" + suo).removeClass();
            $("#glyph_" + suo).addClass("glyphicon glyphicon-remove-circle");
            }
            $("#number_of_selected_claims").text(data_json.selected_count);
            console.log(data_json.selected_for_audit);
        });
    })
    .catch(function(error) {console.log("Fetch error: " + error);
    });
}