"use strict";

$(document).ready(function () {
    hopscotch.startTour({
        id: "ftue",
        steps: [
            {
                target: "loaded-image",
                content: "Here you will see the media included in each new post.",
                placement: "bottom",
                yOffset: 10,
                xOffset: -30,
                arrowOffset: "center"
            },
            {
                target: "prompt",
                content: "Here you will see the caption corresponding to each post.",
                placement: "top",
                zindex: 9999
            },
            {
                target: "fc-dom-1",
                content: "Here is where you can keep track of everything we have scheduled to your social media.",
                placement: "top",
                arrowOffset: "center",
                xOffset: -100,
                zindex: 999
            },
        ],
        showPrevButton: true,
        onEnd: function() {
            console.log("Tour ended!");
            tourDone();
        }
    });
});
