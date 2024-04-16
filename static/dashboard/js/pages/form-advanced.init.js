"use strict";

!function(t){
    function e(){}
    e.prototype.initSelect2 = function() {
        t('[data-toggle="select2"]').select2()
    };
    e.prototype.initSwitchery=function(){
        t('[data-plugin="switchery"]').each(function(e,a){
            new Switchery(a,t(a).data());
        });
    };
    e.prototype.initSelectize = function() {
        t("#selectize-tags").selectize({
            maxItems:2,
            create: false,
            persist: false
        }),
        t("#selectize-tags2").selectize({
            maxItems:3,
            create: false,
            persist: false
        }),
        t("#selectize-select").selectize({
            create: !0,
            sortField: {
                field: "text",
                direction: "asc"
            },
            dropdownParent: "body"
        }),
        t("#selectize-select2").selectize({
            create: !0,
            sortField: {
                field: "text",
                direction: "asc"
            },
            dropdownParent: "body"
        }),
        t(".selectize-close-btn").selectize({
            plugins: ["remove_button"],
            persist: !1,
            create: !0,
            render: {
                item: function(e, a) {
                    return '<div>"' + a(e.text) + '"</div>'
                }
            }
        }),
        t(".selectize-drop-header").selectize({
            sortField: "text",
            hideSelected: !1,
            plugins: {
                dropdown_header: {
                    title: "Language"
                }
            }
        })
    };
    e.prototype.init=function(){
        this.initSelect2(),
        this.initSelectize(),
        this.initSwitchery();
    };
    
    t.FormAdvanced=new e,
    t.FormAdvanced.Constructor=e;
}(window.jQuery),
window.jQuery.FormAdvanced.init();
