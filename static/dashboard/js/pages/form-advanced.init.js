"use strict";

!function(t){
    function e(){}
    
    e.prototype.initSwitchery=function(){
        t('[data-plugin="switchery"]').each(function(e,a){
            new Switchery(a,t(a).data());
        });
    };
    
    e.prototype.init=function(){
        this.initSwitchery();
    };
    
    t.FormAdvanced=new e,
    t.FormAdvanced.Constructor=e;
}(window.jQuery),
window.jQuery.FormAdvanced.init();
