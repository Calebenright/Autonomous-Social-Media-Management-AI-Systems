"use strict";

import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-app.js';
import { getFirestore, collection, doc, setDoc, updateDoc, getDocs, onSnapshot, deleteDoc } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-firestore.js';
import { getAuth, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-auth.js';

var firebaseConfig = {
    apiKey: "AIzaSyCJTdpRMOwfhDosa6MTPbsh38kxxiqllc4",
    authDomain: "feed-ai-c379d.firebaseapp.com",
    projectId: "feed-ai-c379d",
    storageBucket: "feed-ai-c379d.appspot.com",
    messagingSenderId: "825164430085",
    appId: "1:825164430085:web:a41ec57b7c3c0d92c5156c",
    measurementId: "G-0K43VDRKJP"
    };

const firebaseApp = initializeApp(firebaseConfig);
const auth = getAuth(firebaseApp);
const db = getFirestore(firebaseApp);
const userDocRef = doc(collection(db, 'users'), user_id);
const ev = [];
const eventsCollectionRef = collection(userDocRef, "events");

function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

function updateEventInFirestore(info) {
    const {eid, image_url, start, caption, socials, type, status} = info.event.extendedProps;
    const updatedStartTime = info.event.start;
    const eventDocRef = doc(collection(userDocRef, 'events'), eid);

    const eventData = {
        eid,
        start: updatedStartTime,
        image_url,
        caption,
        socials,
        type,
        status
    };

    setDoc(eventDocRef, eventData, { merge: true })
        .then(() => console.log("Event updated successfully."))
        .catch(error => console.error("Error updating event: ", error));
}

// Create a debounced version of updateEventInFirestore
const debouncedEventUpdate = debounce(updateEventInFirestore, 1000);

await getDocs(eventsCollectionRef)
.then((querySnapshot) => {
      querySnapshot.forEach((doc) => {
        var eventData = doc.data();

        var eventObject = {
            eid: eventData.eid,
            start: eventData.start.toDate(),
            image_url: eventData.image_url,
            caption: eventData.caption,
            className: eventData.className,
            socials: eventData.socials,
            type: eventData.type,
            status: eventData.status
        };

        ev.push(eventObject);
      });
    })
    .catch((error) => {
      console.error("Error getting documents from Firestore:", error);
});

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
        this.$time = l("#time"),
        this.$facebook = l("#facebook"),
        this.$linkedin = l("#linkedin"),
        this.$instagram = l("#instagram"),
        this.$socialReset = l("#social_reset"),
        this.$darkButton = l("#dark-button"),
        this.$downloadForm = l("#downloadForm"),
        this.$calendarObj = null,
        this.$selectedEvent = null,
        this.$newEventData = null
    }
    
    e.prototype.onEventClick = function(e) {
        this.$formEvent[0].reset();
        this.$formEvent.removeClass("was-validated");
        this.$newEventData = null;
        this.$btnDeleteEvent.show();
        this.$modalTitle.text("Edit Post");
        this.$eventCaption = l("#event-caption");
        this.$eventImg = l("#event-image");
        this.$time = l("#time");
        this.$selectedEvent = e.event;
        const caption = e.event.extendedProps.caption || "";
        const img = e.event.extendedProps.image_url || "https://storage.googleapis.com/starter_web_app_bucket/assets/ScheduleTextPostCalendarImagePlaceholder.png";
        const originalTimestamp  = e.event.start
        const originalDate = moment(originalTimestamp);
        const originalTimeFormatted = originalDate.format('HH:mm');
        this.$time.val(originalTimeFormatted);
        const socialElements = {
            'facebook': this.$facebook,
            'instagram': this.$instagram,
            'linkedin': this.$linkedin
        };
        this.$facebook.hide();
        this.$instagram.hide();
        this.$linkedin.hide();
        const socials = e.event.extendedProps.socials || [];
        for (let social of socials) {
            const element = socialElements[social];
            if (element) {
                element.show();
            }
        }
        this.$eventCaption.text(caption);
        this.$eventImg.attr("src", img);
        this.$modal.show();
    };
    
    e.prototype.init = function() {

        this.$modal = new bootstrap.Modal(document.getElementById("event-modal"), { keyboard: !1 });
        
        new FullCalendar.Draggable(document.getElementById("external-events"), {
            itemSelector: ".external-event",
            eventData: function(eventEl) {
                return {
                    title: eventEl.innerText,
                    className: l(eventEl).data("class"),
                    image_url: l(eventEl).data("image-url"),
                    socials: l(eventEl).data("socials"),
                    type: l(eventEl).data("type"),
                    status: l(eventEl).data("status")
                };
            }
        });

        var a = this;
        
        a.$calendarObj = new FullCalendar.Calendar(a.$calendar[0], {
            slotDuration: "00:15:00",
            slotMinTime: "08:00:00",
            slotMaxTime: "22:00:00",
            themeSystem: "bootstrap",
            bootstrapFontAwesome: !1,
            buttonText: {
                today: "Today",
                month: "Month",
                prev: "Prev",
                next: "Next",
                list: "List",
                prev: "Prev",
                next: "Next"
            },
            initialView: "dayGridMonth",
            handleWindowResize: !0,
            height: l(window).height() - 200,
            headerToolbar: {
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth,timeGridWeek,timeGridDay,listMonth"
            },
            initialEvents: ev,
            editable: !0,
            droppable: !0,
            selectable: !0,
            dateClick: function(e) {
                // a.onSelect(e)
            },
            eventClick: function(e) {
                a.onEventClick(e)
            },
            eventContent: function (arg) {
                let arrayOfDomNodes = [];
            
                // image event
                let imgEventWrap = document.createElement('div');
                if (arg.event.extendedProps.image_url) {
                    let imgEvent = '<img src="' + arg.event.extendedProps.image_url + '" style="max-width: 95%; height: auto; border-radius: 5px;">';
                    imgEventWrap.classList = "fc-event-img";
                    imgEventWrap.style.padding = "5%";
                    imgEventWrap.innerHTML = imgEvent;
                } else {
                    let imgEvent = '<img src="' + 'https://storage.googleapis.com/starter_web_app_bucket/assets/ScheduleTextPostCalendarImagePlaceholder.png' + '" style="max-width: 95%; height: auto; border-radius: 5px;">';
                    imgEventWrap.classList = "fc-event-img";
                    imgEventWrap.style.padding = "5%";
                    imgEventWrap.innerHTML = imgEvent;
                }

                arrayOfDomNodes = [imgEventWrap];

                return { domNodes: arrayOfDomNodes };
            },

            eventDrop: function (info) {
                debouncedEventUpdate(info);
            },
        });
        
        a.$calendarObj.render();
        
        a.$btnNewEvent.on("click", function(e) {
            a.onSelect({ date: new Date, allDay: !0 })
        });

        a.$facebook.on("click", function(e) {
            if (a.$selectedEvent) {
                a.$facebook.hide();
            }
        });
        
        a.$instagram.on("click", function(e) {
            if (a.$selectedEvent) {
                a.$instagram.hide();
            }
        });
        
        a.$linkedin.on("click", function(e) {
            if (a.$selectedEvent) {
                a.$linkedin.hide();
            }
        });

        a.$socialReset.on("click", function(e) {
            if (a.$selectedEvent) {
                a.$instagram.show();
                a.$facebook.show();
                a.$linkedin.show();
            }
        });
        
        a.$darkButton.on("click", function(e) {
            e.preventDefault();
            window.location.href = downloadUrl;
        });
        
        a.$formEvent.on("submit", function(e) {
            e.preventDefault();
            var t, n = a.$formEvent[0];
            if (n.checkValidity()) {
                if (a.$selectedEvent) {
                    const eid = a.$selectedEvent.extendedProps.eid;
                    const newTime = l("#time").val();
                    let newTimestamp = moment(a.$selectedEvent.start);
                    const [hour, minute] = newTime.split(':').map(Number);
                    newTimestamp.hour(hour);
                    newTimestamp.minute(minute);
                    const eventDocRef = doc(collection(userDocRef, 'events'), eid);
                    const caption = l("#event-caption").text();
                    const socialElements = {
                        'facebook': a.$facebook,
                        'linkedin': a.$linkedin,
                        'instagram': a.$instagram
                    };
                    
                    const socials = [];
                    for (const [social, element] of Object.entries(socialElements)) {
                        if (!element.is(":hidden")) {
                            socials.push(social);
                        }
                    }
                    const eventData = {
                        start: newTimestamp.toDate(),
                        caption: caption,
                        socials: socials,
                    };
                    setDoc(eventDocRef, eventData, { merge: true })
                        .then(() => {
                            
                            a.$selectedEvent.setExtendedProp("caption", l("#event-caption").text());
                            a.$selectedEvent.setStart(newTimestamp.toDate());
                            a.$selectedEvent.setExtendedProp("socials", socials);
                            a.$calendarObj.refetchEvents();
                            a.$modal.hide();
                        })
                        .catch((error) => {
                            console.error('Error updating event to Firestore:', error);
                        });
                }
            } else {
                e.stopPropagation();
                n.classList.add("was-validated");
            }
        });
        
        l(a.$btnDeleteEvent.on("click", function(e) {
            if (a.$selectedEvent) {
                const eid = a.$selectedEvent.extendedProps.eid;
                const eventDocRef = doc(collection(userDocRef, 'events'), eid);
                deleteDoc(eventDocRef)
                    .then(() => {})
                    .catch((error) => {
                        console.error('Error removing event from Firestore:', error);
                    });
                a.$selectedEvent.remove();
                a.$selectedEvent = null;
                a.$modal.hide();
            }
        }));
    };    
    
    l.CalendarApp = new e,
    l.CalendarApp.Constructor = e
}(window.jQuery), window.jQuery.CalendarApp.init();
