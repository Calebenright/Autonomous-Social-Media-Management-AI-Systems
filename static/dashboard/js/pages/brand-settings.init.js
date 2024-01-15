"use strict";

// FIREBASE LISTENER //

import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-app.js';
import { getFirestore, collection, doc, setDoc, getDoc, onSnapshot } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-firestore.js';

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
const statusDocRef = doc(collection(db, 'users'), jsonDump.userId);
const logoSwitch = document.getElementById('logo_switch');

function updateStatusInFirestore() {
    onSnapshot(statusDocRef, (docSnapshot) => {
        if (docSnapshot.exists()) {
            let isLogo = docSnapshot.data().isLogo;

            const userData = {
                isLogo: logoSwitch.checked,
            };

            logoSwitch.checked = isLogo;

            setDoc(statusDocRef, userData, { merge: true })
                .then(() => {
                    console.log('Data updated');
                })
                .catch((error) => {
                    console.error('Error updating data to Firestore:', error);
                });
        } else {
            console.error('No Document Exists:', error);
        }
    }, (error) => {
        console.error('Error in realtime listener:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    onSnapshot(statusDocRef, (docSnapshot) => {
        if (docSnapshot.exists()) {
            let isLogo = docSnapshot.data().isLogo;
            logoSwitch.checked = isLogo;
            console.log(isLogo);
        } else {
            console.error('No Document Exists:', error);
        }
    }, (error) => {
        console.error('Error in realtime listener:', error);
    });
});

if (logoSwitch) logoSwitch.addEventListener('change', updateStatusInFirestore);

!function(i) {
    function e() {
        this.$body = i("body")
    }
    e.prototype.init = function() {
        Dropzone.autoDiscover = false;
        i('[data-plugin="dropzone"]').each(function() {
            var e = i(this).attr("action"),
                o = i(this).data("previewsContainer"),
                e = {
                    url: e
                };
            o && (e.previewsContainer = o);
            var o = i(this).data("uploadPreviewTemplate");
            o && (e.previewTemplate = i(o).html());
            i(this).dropzone(e)
        })
    };
    i.FileUpload = new e();
    i.FileUpload.Constructor = e;
}(window.jQuery);

window.jQuery.FileUpload.init();

0 < $('[data-plugins="dropify"]').length && $('[data-plugins="dropify"]').dropify({
    messages: {
        default: "File Upload",
        replace: "Replace File",
        remove: "Remove",
        error: "Ooops, something wrong appended."
    },
    error: {
        fileSize: "The file size is too big (1M max)."
    }
});

function showSpinner() {
    var loadingOverlay = document.getElementById('loading-overlay');
    var submitButton = document.querySelector('#myForm button[type="submit"]');

    loadingOverlay.style.display = 'flex';
    submitButton.disabled = true;
}

const tagInput = document.getElementById('tagInput');
const tagBubbles = document.getElementById('tagBubbles');
const tags = tagsArray;

tagInput.addEventListener('keydown', function(event) {
if (event.key === 'Enter' || event.key === ',') {
event.preventDefault();
const tagValue = tagInput.value.trim();
if (tagValue) {
addTag(tagValue);
tagInput.value = '';
}
}
});

function addTag(tagValue) {
tags.push(tagValue);
const tagBubble = document.createElement('div');
tagBubble.classList.add('tag-bubble');
tagBubble.textContent = tagValue;
tagBubbles.appendChild(tagBubble);
tagBubble.addEventListener('click', function() {
removeTag(tagValue);
});
}

function removeTag(tagValue) {
const index = tags.indexOf(tagValue);
if (index !== -1) {
tags.splice(index, 1);
updateTagBubbles();
}
}

function updateTagBubbles() {
tagBubbles.innerHTML = '';
tags.forEach(tagValue => {
const tagBubble = document.createElement('div');
tagBubble.classList.add('tag-bubble');
tagBubble.textContent = tagValue;
tagBubbles.appendChild(tagBubble);
tagBubble.addEventListener('click', function() {
removeTag(tagValue);
});
});
}

function updateHiddenInput() {
const tagsInput = document.querySelector('input[name="tags"]');
tagsInput.value = tags.join(',');
}

const tagForm = document.getElementById('tagForm');
tagForm.addEventListener('submit', function(event) {
updateHiddenInput();
tagForm.submit();
});

updateTagBubbles();
