function submit_message() {

    var title = document.getElementById("title");
    var message = document.getElementById("message");

    var entry = {
        title: title.value,
        message: message.value
    };
    
    fetch(`${url_for_create_entry}`, {  // use global var defined in base.html
        method: "POST",
        credentials: "include",
        body: JSON.stringify(entry),
        cache: "no-cache",
        headers: new Headers({"content-type": "application/json"})
    })
    .then(function (response) {
        if (response.status !== 200) {
            console.log(`Looks like there was a problem. Status code: ${response.status}`);
            return;
        }
        response.text().then(function (data) {
            title.value = "";
            message.value = "";
            $( data ).appendTo( ".sandbox" );
            console.log(data);
        });
    })
    .catch(function(error) {console.log("Fetch error: " + error);
    });   
}

function specify_comment_target(order=-1,item=-1) {
    var comment_parent_label = document.getElementById("comment_parent");
    if (order !== -1) {
        comment_parent_label.innerText = "SalesOrder #" + order
    } else if (item != -1) {
        comment_parent_label.innerText = "SalesItem #" + item
    } 
}

function submit_reply() {

    var reply_title = document.getElementById("reply_title");
    var reply_message = document.getElementById("reply_message");
    var reply_og_sand = document.getElementById("reply_og_sand");

    var entry = {
        title: reply_title.value,
        message: reply_message.value,
	    og_sand: reply_og_sand.innerText
    };
    
    fetch(`${url_for_create_reply}`, {  // use global var defined in base.html
        method: "POST",
        credentials: "include",
        body: JSON.stringify(entry),
        cache: "no-cache",
        headers: new Headers({"content-type": "application/json"})
    })
    .then(function (response) {
        if (response.status !== 200) {
            console.log(`Looks like there was a problem. Status code: ${response.status}`);
            return;
        }
        response.text().then(function (data) {
            reply_title.value = "";
            reply_message.value = "";
            $( data ).appendTo( "#sand-" + reply_og_sand.innerText + "-reply"  );
            console.log(data);
        });
    })
    .catch(function(error) {console.log("Fetch error: " + error);
    });   
}