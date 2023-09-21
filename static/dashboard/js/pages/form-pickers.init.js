"use strict";

!function(t) {
    function e() {}

    e.prototype.init = function() {
        t("#colorpicker-showinput-intial").spectrum({
            showInitial: !0,
            showInput: !0
        });
    },

    t.FormPickers = new e,
    t.FormPickers.Constructor = e
}(window.jQuery),
    window.jQuery.FormPickers.init();

    