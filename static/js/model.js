var FriendModel = function(elements) {
    this.friendView = new FriendView(elements);
    //this.friends = [];
    var self = this;

    this.initCallback = function(response) {
        var error = "";
        if(response.error != "") {
            error = response.error;
        }
        self.friendView.populate(response.reply_data, error);
    };

    this.addFriendCallback = function(response) {
        var error = "";
        if(response.error != "") {
            error = response.error;
        } else if(!response.reply_data.exists) {
            error = "The friend you are trying to add does not exist.";
        }
        self.friendView.updateView(response.reply_data.user_id, true, error);
    };

    this.removeFriendCallback = function(response) {
        var error = "";
        if(response.error != "") {
            error = response.error;
            self.friendView.updateView(null, false, error);
            return;
        } else {
            self.init();
        }
    };
};

_.extend(FriendModel.prototype, {
    init: function() {
        ajax({"protocol_version": PROTOCOL_VERSION, "message_id": null, "user_id": getCookie("user_id"), "command": "get_friends", "command_data": {"user_id": getCookie("user_id")} }, this.initCallback);
    },

    addFriend: function(userid) {
        ajax({"protocol_version": PROTOCOL_VERSION, "message_id": null, "user_id": getCookie("user_id"), "command": "add_friend_if_exists", "command_data": {"user_id": userid} }, this.addFriendCallback);
    },

    removeFriend: function(userid) {
        ajax({"protocol_version": PROTOCOL_VERSION, "message_id": null, "user_id": getCookie("user_id"), "command": "remove_friend", "command_data": {"user_id": userid} }, this.removeFriendCallback);
    }
});

var SupsModel = function(elements) {
    this.supsView = new SupsView(elements);

    this.currentIndex = -1;
    this.sups = [];

    var self = this;

    this.initCallback = function(response) {
        self.sups = response.reply_data;
        self.currentIndex = self.sups.length - 1;
        self.supsView.show(self.sups, self.currentIndex, response.error);
        if(self.sups != undefined) {
            self.supsView.updateCount(self.sups.length);
        }
    };

    this.updateSupsCallback = function(response) {
        self.sups = response.reply_data;
        self.supsView.updateCount(self.sups.length);
    };

    this.removeSupCallback = function(response) {
        if(response.reply_data == "Removed sup") {
            self.sups = _.without(self.sups, self.sups[self.currentIndex]);
            self.supsView.updateCount(self.sups.length);
            if(self.sups.length == 0) {
                self.currentIndex--;
            } else if(self.currentIndex >= self.sups.length) {
                self.currentIndex--;
                self.supsView.show(self.sups, self.currentIndex, "");
            } else {
                self.supsView.show(self.sups, self.currentIndex, "");
            }
            document.getElementById("delete_sup").disabled = false;
        }
    };

    this.sendSupCallback = function(response) {
        if(response.error) {
            showErrorAlert("Sending sup failed");
        } else {
            showSuccessAlert("You have successfully sent a sup");
        }
    };
};

_.extend(SupsModel.prototype, {
    init: function() {
        ajax({"protocol_version": PROTOCOL_VERSION, "message_id": null, "user_id": getCookie("user_id"), "command": "get_sups", "command_data": null}, this.initCallback);
    },

    updateSups: function() {
        backgroundAjax({"protocol_version": PROTOCOL_VERSION, "message_id": null, "user_id": getCookie("user_id"), "command": "get_sups", "command_data": null}, this.updateSupsCallback);
    },

    prevSup: function() {
        if(this.currentIndex != 0 && this.currentIndex != -1) {
            this.currentIndex--;
        } else {
            return;
        }
        this.supsView.show(this.sups, this.currentIndex, "");
    },

    deleteSup: function() {
        document.getElementById("delete_sup").disabled = true;
        ajax({"protocol_version": PROTOCOL_VERSION, "message_id": null, "user_id": getCookie("user_id"), "command": "remove_sup", "command_data": {"sup_id": this.sups[this.currentIndex].sup_id}}, this.removeSupCallback);
    },

    nextSup: function() {
        if(this.sups.length > this.currentIndex + 1) {
            this.currentIndex++;
        } else {
            return;
        }
        this.supsView.show(this.sups, this.currentIndex, "");
    },

    countSups: function() {
        return sups.length;
    },

    sendSup: function(userid) {
        ajax({"protocol_version": PROTOCOL_VERSION, "message_id": null, "user_id": getCookie("user_id"), "command": "send_sup", "command_data": {"user_id": userid, "sup_id": generateUUID(), "date": _.now()}}, this.sendSupCallback);
    }
});