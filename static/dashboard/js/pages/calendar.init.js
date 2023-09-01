"use strict";

!function(l) {
    function e() {
        this.$body = l("body"),
        this.$modal = l("#event-modal"),
        this.$calendar = l("#calendar"),
        this.$formEvent = l("#form-event"),
        this.$btnNewEvent = l("#btn-new-event"),
        this.$btnDeleteEvent = l("#btn-delete-event"),
        this.$btnSaveEvent = l("#btn-save-event"),
        this.$modalTitle = l("#modal-title"),
        this.$calendarObj = null,
        this.$selectedEvent = null,
        this.$newEventData = null
    }
    
    e.prototype.onEventClick = function(e) {
        this.$formEvent[0].reset(),
        this.$formEvent.removeClass("was-validated"),
        this.$newEventData = null,
        this.$btnDeleteEvent.show(),
        this.$modalTitle.text("Edit Event"),
        this.$modal.show(),
        this.$selectedEvent = e.event,
        l("#event-title").val(this.$selectedEvent.title),
        l("#event-category").val(this.$selectedEvent.classNames[0])
    };
    
    e.prototype.onSelect = function(e) {
        this.$formEvent[0].reset(),
        this.$formEvent.removeClass("was-validated"),
        this.$selectedEvent = null,
        this.$newEventData = e,
        this.$btnDeleteEvent.hide(),
        this.$modalTitle.text("Add New Event"),
        this.$modal.show(),
        this.$calendarObj.unselect()
    };
    
    e.prototype.init = function() {
        this.$modal = new bootstrap.Modal(document.getElementById("event-modal"), { keyboard: !1 });
        var e = new Date(l.now());
        
        new FullCalendar.Draggable(document.getElementById("external-events"), {
            itemSelector: ".external-event",
            eventData: function(eventEl) {
                return {
                    title: eventEl.innerText,
                    className: l(eventEl).data("class"),
                    image_url: l(eventEl).data("image-url") // Add the image_url attribute
                };
            }
        });
        
        var e = [
            {
                start: new Date(l.now() + 158e6),
                image_url: "https://play-lh.googleusercontent.com/IeNJWoKYx1waOhfWF6TiuSiWBLfqLb18lmZYXSgsH1fvb8v1IYiZr5aYWe0Gxu-pVZX3",
                className: "bg-primary"
            },
        ];
        
        var a = this;
        
        a.$calendarObj = new FullCalendar.Calendar(a.$calendar[0], {
            slotDuration: "00:15:00",
            slotMinTime: "08:00:00",
            slotMaxTime: "19:00:00",
            themeSystem: "bootstrap",
            bootstrapFontAwesome: !1,
            buttonText: {
                today: "Today",
                month: "Month",
                prev: "Prev",
                next: "Next"
            },
            initialView: "dayGridMonth",
            handleWindowResize: !0,
            height: l(window).height() - 200,
            headerToolbar: {
                left: "prev,next today",
                center: "title",
                right: ""
            },
            initialEvents: e,
            editable: !0,
            droppable: !0,
            selectable: !0,
            dateClick: function(e) {
                a.onSelect(e)
            },
            eventClick: function(e) {
                a.onEventClick(e)
            },
            eventContent: function (arg) {
                let arrayOfDomNodes = [];
            
                // title event
                let titleEvent = document.createElement('div');
                if (arg.event._def.title) {
                    titleEvent.innerHTML = arg.event._def.title;
                    titleEvent.classList = "fc-event-title fc-sticky";
                }
            
                // image event
                let imgEventWrap = document.createElement('div');
                if (arg.event.extendedProps.image_url) {
                    let imgEvent = '<img src="' + arg.event.extendedProps.image_url + '" style="max-width: 80%; height: auto; border-radius: 5px;">'; // Adjust max-width and height as needed
                    imgEventWrap.classList = "fc-event-img";
                    imgEventWrap.innerHTML = imgEvent;
                }
            
                arrayOfDomNodes = [titleEvent, imgEventWrap];
            
                return { domNodes: arrayOfDomNodes };
            },
        });
        
        a.$calendarObj.render();
        
        a.$btnNewEvent.on("click", function(e) {
            a.onSelect({ date: new Date, allDay: !0 })
        });
        
        a.$formEvent.on("submit", function(e) {
            e.preventDefault();
            var t, n = a.$formEvent[0];
            if (n.checkValidity()) {
                if (a.$selectedEvent) {
                    a.$selectedEvent.setProp("title", l("#event-title").val());
                    a.$selectedEvent.setProp("classNames", [l("#event-category").val()]);
                } else {
                    t = {
                        title: l("#event-title").val(),
                        start: a.$newEventData.date,
                        allDay: a.$newEventData.allDay,
                        className: l("#event-category").val()
                    };
                    a.$calendarObj.addEvent(t);
                }
                a.$modal.hide();
            } else {
                e.stopPropagation();
                n.classList.add("was-validated");
            }
        });
        
        l(a.$btnDeleteEvent.on("click", function(e) {
            if (a.$selectedEvent) {
                a.$selectedEvent.remove();
                a.$selectedEvent = null;
                a.$modal.hide();
            }
        }));
    };
    
    l.CalendarApp = new e,
    l.CalendarApp.Constructor = e
}(window.jQuery), window.jQuery.CalendarApp.init();
