var PROTOCOL_VERSION = "1.3";
var SERVER_URL = "http://localhost:8080/post";

var MODAL = undefined;

var loadUp = false;

window.addEventListener('load', function() {
    // Place your Wassup app code here
    console.log("Wassup?");

    var fullname  = "";

    var supCanvas = document.getElementById("sup_message");

    var mobileFriendList = document.getElementById("mobile_friend_list");
    var desktopFriendList = document.getElementById("desktop_friend_list");
    var friendModel = new FriendModel({mobileFriendList: mobileFriendList, desktopFriendList: desktopFriendList});

    // Initialize friend model
    friendModel.init();

    var supsModel = new SupsModel({canvas: supCanvas, desktopSupCount: document.getElementById("desktop_sup_count")});

    // Initialize sup model
    supsModel.init();

    document.getElementById("add_friend_btn").addEventListener('click', function() {
        friendModel.addFriend(document.getElementById("add_friend_text").value);
    });

    document.getElementById("desktopSupFriends").addEventListener('click', function() {
        var options = desktopFriendList.options
        var selected = [];
        for(var i = 0; i < options.length; i++) {
            if(options[i].selected) {
                selected.push(options[i].value);
                options[i].selected = false;
            }
        }
        for(var i = 0; i < selected.length; i++) {
            supsModel.sendSup(selected[i]);
        }
    });

    document.getElementById("desktopRemoveFriends").addEventListener('click', function() {
        var options = desktopFriendList.options
        var selected = [];
        for(var i = 0; i < options.length; i++) {
            if(options[i].selected) {
                selected.push(options[i].value);
                options[i].selected = false;
            }
        }
        for(var i = 0; i < selected.length; i++) {
            friendModel.removeFriend(selected[i]);
        }
    });

    document.getElementById("prev_sup").addEventListener('click', function() {
        supsModel.prevSup();
    });

    document.getElementById("next_sup").addEventListener('click', function() {
        supsModel.nextSup();
    });

    document.getElementById("delete_sup").addEventListener('click', function() {
        supsModel.deleteSup();
    });


    var pubAccountCreateCallback = function(response) {
        // Re-init models.
        friendModel.init();
        supsModel.init();
    };

    document.getElementById("public_selected").addEventListener('click', function(event) {
        event.preventDefault();

        // Change Server URL
        SERVER_URL = "http://104.197.3.113/post";

        // Better to just create account each time instead of first checking if user exists then create account if it doesn't. End result will be same.
        ajax({
            "protocol_version": PROTOCOL_VERSION,
            "message_id": null,
            "user_id": getCookie("user_id"),
            "command": "create_user",
            "command_data": {"user_id": getCookie("user_id"), "full_name": fullname}
        }, pubAccountCreateCallback);

        // Change what server we're using in UI
        document.getElementById("current_server").innerHTML = "Public Server";
    });

    document.getElementById("private_selected").addEventListener('click', function() {
        SERVER_URL = "http://localhost:8080/post";

        // Change what server we're using in UI
        document.getElementById("current_server").innerHTML = "Private Server";

        // Re-init models.
        friendModel.init();
        supsModel.init();
    });

    document.getElementById("mobile_send_sup").addEventListener('click', function() {
        supsModel.sendSup(mobileFriendList.value);
    });

    ajax({
        "protocol_version": PROTOCOL_VERSION,
        "message_id": null,
        "user_id": getCookie("user_id"),
        "command": "user_exists",
        "command_data": {"user_id": getCookie("user_id")}
    }, function(response) {
        fullname = response.reply_data.full_name;
    });

    setInterval(function() {
        supsModel.updateSups();
    }, 60000);

    //handleAjaxRequest();
});

function showSuccessAlert(message) {
    var container = document.createElement('div');
    var alertEle = document.importNode(document.getElementById("success_alert_template").content, true);
    var appContainer = document.getElementById("app_container");
    container.appendChild(alertEle);
    container.getElementsByClassName("alert_message")[0].innerText = message;
    appContainer.insertBefore(container, appContainer.firstChild );
}

function showErrorAlert(message) {
    var container = document.createElement('div');
    var alertEle = document.importNode(document.getElementById("error_alert_template").content, true);
    var appContainer = document.getElementById("app_container");
    container.appendChild(alertEle);
    container.getElementsByClassName("alert_message")[0].innerText = message;
    appContainer.insertBefore(container, appContainer.firstChild );
}

// From Piazza
function generateUUID(){
    var d = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
};

// Get cookie from http://www.w3schools.com/js/js_cookies.asp
function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i<ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
    }
    return "";
}

// Example derived from: https://developer.mozilla.org/en-US/docs/AJAX/Getting_Started
// This one does not pop up loading
function backgroundAjax(toSend, callback) {

    // Create the request object
    var httpRequest = new XMLHttpRequest();

    // Set the function to call when the state changes
    httpRequest.addEventListener('readystatechange', function() {

        // These readyState 4 means the call is complete, and status
        // 200 means we got an OK response from the server
        if (httpRequest.readyState === 4 && httpRequest.status === 200) {
            // Parse the response text as a JSON object
            callback(JSON.parse(httpRequest.responseText));
        }
    });

    // This opens a POST connection with the server at the given URL
    httpRequest.open('POST', SERVER_URL);

    // Set the data type being sent as JSON
    httpRequest.setRequestHeader('Content-Type', 'application/json');

    // Send the JSON object, serialized as a string
    //var objectToSend = {"protocol_version": "1.2", "message_id": null, "command": "user_exists", "command_data": {"user_id": "kpatel"}};
    httpRequest.send(JSON.stringify(toSend));
}


// Example derived from: https://developer.mozilla.org/en-US/docs/AJAX/Getting_Started
function ajax(toSend, callback) {

    // Create the request object
    var httpRequest = new XMLHttpRequest();

    // Set the function to call when the state changes
    httpRequest.addEventListener('readystatechange', function() {

        // These readyState 4 means the call is complete, and status
        // 200 means we got an OK response from the server
        if (httpRequest.readyState === 4 && httpRequest.status === 200) {
            // Parse the response text as a JSON object
            callback(JSON.parse(httpRequest.responseText));
            hideLoad();
        }
    });

    // This opens a POST connection with the server at the given URL
    httpRequest.open('POST', SERVER_URL);

    // Set the data type being sent as JSON
    httpRequest.setRequestHeader('Content-Type', 'application/json');

    // Send the JSON object, serialized as a string
    //var objectToSend = {"protocol_version": "1.2", "message_id": null, "command": "user_exists", "command_data": {"user_id": "kpatel"}};
    showLoad();
    httpRequest.send(JSON.stringify(toSend));
}

/**
 * From http://stackoverflow.com/questions/1527803/generating-random-numbers-in-javascript-in-a-specific-range
 * Returns a random integer between min (inclusive) and max (inclusive)
 * Using Math.round() will give you a non-uniform distribution!
 */
function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function showLoad() {
    if (!loadUp) {
        $('#basicModal').modal({backdrop: "static", keyboard: false});
        loadUp = true;
    }
}

function hideLoad() {
    if(loadUp) {
        $('#basicModal').modal("hide");
        loadUp = false;
    }
}