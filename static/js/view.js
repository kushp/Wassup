'use strict';

var FriendView = function(elements) {
    this.elements = elements;
};

_.extend(FriendView.prototype, {
    populate: function(friends, error) {
        if(error != "") {
            showErrorAlert(error);
            return;
        }
        // clear first
        for(var i = this.elements.desktopFriendList.options.length-1; i > -1; i--) {
            if(i < 0) break;
            this.elements.desktopFriendList.remove(i);
            this.elements.mobileFriendList.remove(i);
        }
        for(var i = 0; i < friends.length; i++) {
            var newFriendOption = document.createElement("option");
            newFriendOption.text = friends[i].user_id;
            newFriendOption.value = friends[i].user_id;
            var newFriendOption2 = document.createElement("option");
            newFriendOption2.text = friends[i].user_id;
            newFriendOption2.value = friends[i].user_id;
            this.elements.mobileFriendList.add(newFriendOption);
            this.elements.desktopFriendList.add(newFriendOption2);
        }
    },

    updateView: function(friend, add, error) {
        if(error != "") {
            showErrorAlert(error);
            return;
        }
        if(add) {
            var newFriendOption = document.createElement("option");
            newFriendOption.text = friend;
            newFriendOption.value = friend;
            var newFriendOption2 = document.createElement("option");
            newFriendOption2.text = friend;
            newFriendOption2.value = friend;
            this.elements.mobileFriendList.add(newFriendOption);
            this.elements.desktopFriendList.add(newFriendOption2);
        }
    }
});

var SupsView = function(elements) {
    this.elements = elements;
};

_.extend(SupsView.prototype, {
    show: function(sups, index, error) {
        if(error) {
            showErrorAlert(error);
            return;
        }
        if(index == -1) {
            var ctx = this.elements.canvas.getContext("2d");
            ctx.clearRect(0, 0, this.elements.canvas.width, this.elements.canvas.height );
            ctx.font = "16px Arial";
            ctx.fillStyle = 'purple';
            ctx.textAlign="center";
            ctx.fillText("You have no sups!", this.elements.canvas.width/2, this.elements.canvas.height - 20);
            return;
        }
        var sup_data = sups[index];
        var ctx = this.elements.canvas.getContext("2d");

        ctx.save();
        ctx.clearRect(0, 0, this.elements.canvas.width, this.elements.canvas.height );

        ctx.font = "16px Arial";
        ctx.fillStyle = 'purple';
        ctx.textAlign="center";
        ctx.fillText("Sent by " + sup_data.sender_id + " at " + new Date(sup_data.date).toLocaleString(), this.elements.canvas.width/2, this.elements.canvas.height - 20);

        // Randomize font
        var bold = Math.floor(Math.random() * 2) == 1 ? " bold" : "";
        var italics = Math.floor(Math.random() * 2) == 1 ? " italic" : "";
        var fontSize = 40 + Math.floor(Math.random() * 120);
        ctx.font = fontSize+ "px Arial" + bold + italics;

        // Random little rotation
        ctx.rotate(getRandomInt(-10, 10) * Math.PI/180);

        // random colour snipplet http://stackoverflow.com/questions/7266261/is-it-not-possible-to-generate-random-numbers-directly-inside-a-fillstyle
        ctx.fillStyle = "rgb("+ Math.floor(Math.random()*256)+","+ Math.floor(Math.random()*256)+","+ Math.floor(Math.random()*256)+")";

        ctx.textAlign = "center";
        ctx.fillText("Sup?", this.elements.canvas.width/2, this.elements.canvas.height/2);
        ctx.restore();
    },

    updateCount: function(supCount) {
        this.elements.desktopSupCount.innerText = supCount;
    }
});