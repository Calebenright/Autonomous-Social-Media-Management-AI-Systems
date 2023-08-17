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
            eventData: function(e) {
                return {
                    title: e.innerText,
                    className: l(e).data("class")
                };
            }
        });

        var e = [
            { title: "Meeting with Mr. Shreyu", start: new Date(l.now() + 158e6), end: new Date(l.now() + 338e6), className: "bg-warning" },
            // ... other event objects
        ];

        var a = this;

        a.$calendarObj = new FullCalendar.Calendar(a.$calendar[0], {
            // Calendar configuration options
        });

        a.$calendarObj.render();

        a.$btnNewEvent.on("click", function (e) {
            a.onSelect({ date: new Date, allDay: !0 });
        });

        // ... more event handlers

    };

    l.CalendarApp = new e,
    l.CalendarApp.Constructor = e;
}(window.jQuery);

window.jQuery.CalendarApp.init();
