"use strict";

import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-app.js';
import { getFirestore, collection, doc, setDoc, updateDoc, getDocs, onSnapshot, deleteDoc } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-firestore.js';

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
const db = getFirestore(firebaseApp);
const userDocRef = doc(collection(db, 'users'), user_id);
const ev = [];
const eventsCollectionRef = collection(userDocRef, "events");

// new Date('2023-12-02T14:30:00')

await getDocs(eventsCollectionRef)
.then((querySnapshot) => {
      querySnapshot.forEach((doc) => {
        var eventData = doc.data();

        var eventObject = {
            eid: eventData.eid,
            start: eventData.start.toDate(),
            image_url: eventData.image_url,
            caption: eventData.caption,
            className: eventData.className
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
        this.$selectedEvent = e.event;
        const caption = e.event.extendedProps.caption || "";
        const img = e.event.extendedProps.image_url || "https://user-images.githubusercontent.com/101482/29592647-40da86ca-875a-11e7-8bc3-941700b0a323.png";
        this.$eventCaption.text(caption);
        this.$eventImg.attr("src", img);
        this.$modal.show();
    };
    
    // e.prototype.onSelect = function(e) {
    //     this.$formEvent[0].reset(),
    //     this.$formEvent.removeClass("was-validated"),
    //     this.$selectedEvent = null,
    //     this.$newEventData = e,
    //     this.$btnDeleteEvent.hide(),
    //     this.$modalTitle.text("Add New Event"),
    //     this.$modal.show(),
    //     this.$calendarObj.unselect()
    // };
    
    e.prototype.init = function() {

        this.$modal = new bootstrap.Modal(document.getElementById("event-modal"), { keyboard: !1 });
        
        new FullCalendar.Draggable(document.getElementById("external-events"), {
            itemSelector: ".external-event",
            eventData: function(eventEl) {
                return {
                    title: eventEl.innerText,
                    className: l(eventEl).data("class"),
                    image_url: l(eventEl).data("image-url")
                };
            }
        });
        
        console.log("Events from Firestore:", ev);

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
                }

                // // title event (caption)
                // let titleEvent = document.createElement('div');
                // if (arg.event.extendedProps.caption) {
                //     const words = arg.event.extendedProps.caption.split(' ');
            
                //     // Take the first few words (e.g., the first two words)
                //     const numberOfWordsToDisplay = 5;
                //     const caption = words.slice(0, numberOfWordsToDisplay).join(' ');
            
                //     // Create a square element for the caption
                //     const captionSquare = document.createElement('div');
                //     captionSquare.textContent = caption;
                //     captionSquare.classList = "fc-event-caption";
                //     captionSquare.style.fontWeight = "bold";
                //     captionSquare.style.fontSize = "10px";  
                //     captionSquare.style.color = "#000000";  
                //     captionSquare.style.padding = "5px";   
                //     captionSquare.style.backgroundColor = "#ffffff"; 
                //     captionSquare.style.borderRadius = "5px";
                //     captionSquare.style.whiteSpace = "normal";
                //     captionSquare.style.margin = "10px";   

                //     titleEvent.appendChild(captionSquare);
        
                // }
            
                // arrayOfDomNodes = [imgEventWrap, titleEvent];
            
                // return { domNodes: arrayOfDomNodes };

                arrayOfDomNodes = [imgEventWrap];

                return { domNodes: arrayOfDomNodes };
            },

            eventDrop: function (info) {
        
                var eid = info.event.extendedProps.eid;
                var image_url = info.event.extendedProps.image_url;
                var updatedStartTime = info.event.start;
                var caption = info.event.extendedProps.caption;

                const eventDocRef = doc(collection(userDocRef, 'events'), eid);

                const eventData = {
                    eid: eid,
                    start: updatedStartTime,
                    image_url: image_url,
                    caption: caption
                };

                setDoc(eventDocRef, eventData, { merge: true })
                    .then(() => {
                        console.log("Event updated or set in Firestore");
                    })
                    .catch(error => {
                        console.error("Error updating or setting event in Firestore: ", error);
                    });
                
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
                    const eid = a.$selectedEvent.extendedProps.eid;
                    const eventDocRef = doc(collection(userDocRef, 'events'), eid);
                    const caption = l("#event-caption").val();
                    console.log(caption)
                    const eventData = {
                        caption: caption
                    };
                    setDoc(eventDocRef, eventData, { merge: true })
                        .then(() => {
                            console.log('Event updated');
                        })
                        .catch((error) => {
                            console.error('Error updating event to Firestore:', error);
                        });
                    a.$selectedEvent.setExtendedProp("caption", l("#event-caption").text());
                }
                a.$modal.hide();
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
                    .then(() => {
                        console.log('Event removed from Firestore');
                    })
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
