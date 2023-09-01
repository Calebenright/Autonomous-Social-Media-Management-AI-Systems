"use strict";

!(function ($) {
    function CalendarApp() {
        this.$body = $("body");
        this.$modal = $("#event-modal");
        this.$calendar = $("#calendar");
        this.$formEvent = $("#form-event");
        this.$btnNewEvent = $("#btn-new-event");
        this.$btnDeleteEvent = $("#btn-delete-event");
        this.$btnSaveEvent = $("#btn-save-event");
        this.$modalTitle = $("#modal-title");
        this.$calendarObj = null;
        this.$selectedEvent = null;
        this.$newEventData = null;
        this.$draggedCardData = null;
    }

    CalendarApp.prototype.onEventClick = function (e) {
        this.$formEvent[0].reset();
        this.$formEvent.removeClass("was-validated");
        this.$newEventData = null;
        this.$btnDeleteEvent.show();
        this.$modalTitle.text("Edit Event");
        this.$modal.show();
        this.$selectedEvent = e.event;
        $("#event-title").val(this.$selectedEvent.title);
        $("#event-category").val(this.$selectedEvent.classNames[0]);
    };



    CalendarApp.prototype.init = function () {
        this.$modal = new bootstrap.Modal(document.getElementById("event-modal"), { keyboard: !1 });
        var currentDate = new Date(l.now());
        
        new FullCalendar.Draggable(document.getElementById("external-events"), {
            itemSelector: ".external-event",
            eventData: function(e) {
                return {
                    title: e.innerText,
                    className: l(e).data("class")
                }
            }
        });
        
        var initialEvents = [
            { start: new Date(currentDate.getTime() + 338e6), image_url: "https://play-lh.googleusercontent.com/IeNJWoKYx1waOhfWF6TiuSiWBLfqLb18lmZYXSgsH1fvb8v1IYiZr5aYWe0Gxu-pVZX3", className: "bg-success" },
            // { title: "Interview - Backend Engineer", start: currentDate, end: currentDate, className: "bg-success" },
            // { title: "Phone Screen - Frontend Engineer", start: new Date(currentDate.getTime() + 168e6), className: "bg-info" },
            // { title: "Buy Design Assets", start: new Date(currentDate.getTime() + 338e6), end: new Date(currentDate.getTime() + 4056e5), className: "bg-primary" }
        ];

        var self = this;

        var draggableCards = document.querySelectorAll('.draggable-card');
        draggableCards.forEach(function (card) {
            card.addEventListener('dragstart', function (event) {
                // Store the card's data to use during drop
                self.$draggedCardData = {
                    id: card.getAttribute('data-card-id'),
                    title: card.textContent.trim()
                };
                event.dataTransfer.setData('text/plain', ''); // Required for drag-and-drop to work
            });
        });

        // Attach drop event to the FullCalendar element
        self.$calendar.on('dragover', function (event) {
            event.preventDefault(); // Allow dropping
        });

        self.$calendar.on('drop', function (event) {
            event.preventDefault();
            // Get the dragged card's data
            var cardData = JSON.parse(event.dataTransfer.getData('text/plain'));

            // Get the date from the FullCalendar event (click or drop)
            var selectedDate = self.$selectedEvent ? self.$selectedEvent.date : self.$newEventData.date;

            // Create a new event for the dropped card
            var eventData = {
                title: cardData.title,
                start: selectedDate,
                classNames: ['bg-info'], // Customize class as needed
                cardId: cardData.id // Store card ID in custom property
            };

            // Add the event to the calendar
            self.$calendarObj.addEvent(eventData);

            // Rerender the calendar to update the view
            self.$calendarObj.render();
        });

        self.$calendarObj = new FullCalendar.Calendar(self.$calendar[0], {
            slotDuration: "00:15:00",
            slotMinTime: "08:00:00",
            slotMaxTime: "19:00:00",
            themeSystem: "bootstrap",
            bootstrapFontAwesome: false,
            buttonText: { today: "Today", month: "Month", week: "Week", day: "Day", list: "List", prev: "Prev", next: "Next" },
            initialView: "dayGridMonth",
            handleWindowResize: true,
            height: $(window).height() - 200,
            headerToolbar: {
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth,timeGridWeek,timeGridDay,listMonth"
            },
            initialEvents: initialEvents,
            editable: true,
            droppable: true,
            selectable: true,
            dateClick: function (e) {
                self.onSelect(e);
            },
            eventClick: function (e) {
                self.onEventClick(e);
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

        self.$calendarObj.render();

        self.$btnNewEvent.on("click", function (e) {
            self.onSelect({ date: new Date(), allDay: true });
        });

        self.$formEvent.on("submit", function (e) {
            e.preventDefault();
            var form = self.$formEvent[0];
            if (form.checkValidity()) {
                if (self.$selectedEvent) {
                    self.$selectedEvent.setProp("title", $("#event-title").val());
                    self.$selectedEvent.setProp("classNames", [$("#event-category").val()]);
                } else {
                    var eventData = {
                        title: $("#event-title").val(),
                        start: self.$newEventData.date,
                        allDay: self.$newEventData.allDay,
                        className: $("#event-category").val()
                    };
                    self.$calendarObj.addEvent(eventData);
                }
                self.$modal.hide();
            } else {
                e.stopPropagation();
                form.classList.add("was-validated");
            }
        });

        self.$btnDeleteEvent.on("click", function (e) {
            if (self.$selectedEvent) {
                self.$selectedEvent.remove();
                self.$selectedEvent = null;
                self.$modal.hide();
            }
        });
    };

    $.CalendarApp = new CalendarApp();
    $.CalendarApp.init();
})(window.jQuery);
