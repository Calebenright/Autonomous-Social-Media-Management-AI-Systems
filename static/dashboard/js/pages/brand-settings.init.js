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

// const isLinkedin = userSettings.isLinkedin === true;
// const isFacebook = userSettings.isFacebook === true;
// const isInstagram = userSettings.isInstagram === true;
// const isGoogle = userSettings.isGoogle === true;

const firebaseApp = initializeApp(firebaseConfig);
const db = getFirestore(firebaseApp);
const statusDocRef = doc(collection(db, 'users'), jsonDump.userId);
const linkedinSwitch = document.getElementById('linkedin_switch');
const facebookSwitch = document.getElementById('facebook_switch');
const googleSwitch = document.getElementById('google_business_switch');
const instagramSwitch = document.getElementById('instagram_switch');

function updateStatusInFirestore() {
    onSnapshot(statusDocRef, (docSnapshot) => {
        if (docSnapshot.exists()) {
            let isLinkedin = docSnapshot.data().isLinkedin;
            let isFacebook = docSnapshot.data().isFacebook;
            let isInstagram = docSnapshot.data().isInstagram;
            let isGoogle = docSnapshot.data().isGoogle;

            const userData = {
                isLinkedin: linkedinSwitch.checked,
                isFacebook: facebookSwitch.checked,
                isInstagram: instagramSwitch.checked,
                isGoogle: googleSwitch.checked
            };

            linkedinSwitch.checked = isLinkedin;
            facebookSwitch.checked = isFacebook;
            instagramSwitch.checked = isInstagram;
            googleSwitch.checked = isGoogle;

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
            let isLinkedin = docSnapshot.data().isLinkedin;
            let isFacebook = docSnapshot.data().isFacebook;
            let isInstagram = docSnapshot.data().isInstagram;
            let isGoogle = docSnapshot.data().isGoogle;
            linkedinSwitch.checked = isLinkedin;
            facebookSwitch.checked = isFacebook;
            instagramSwitch.checked = isInstagram;
            googleSwitch.checked = isGoogle;
            console.log(isFacebook);
            console.log(isInstagram);
            console.log(isGoogle);
            console.log(isLinkedin);
        } else {
            console.error('No Document Exists:', error);
        }
    }, (error) => {
        console.error('Error in realtime listener:', error);
    });
});

if (linkedinSwitch) linkedinSwitch.addEventListener('change', updateStatusInFirestore);
if (facebookSwitch) facebookSwitch.addEventListener('change', updateStatusInFirestore);
if (instagramSwitch) instagramSwitch.addEventListener('change', updateStatusInFirestore);
if (googleSwitch) googleSwitch.addEventListener('change', updateStatusInFirestore);

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

// -------------------- IMAGE TAGS ------------------------ //


const imageTagThumbnails = document.getElementById('imageTagThumbnails');
const imageTags = imageTagsArray;

// document.getElementById('imageUpload').addEventListener('change', function(event) {
//     // Iterate over all selected files
//     Array.from(event.target.files).forEach(file => {
//         const reader = new FileReader();
//         reader.onload = function() {
//             addImageTag(reader.result);
//         }
//         reader.readAsDataURL(file);
//     });
// });

function addImageTag(imageUrl) {
    imageTags.push(imageUrl);
    const imageThumbnail = document.createElement('div');
    imageThumbnail.classList.add('image-tag-thumbnail');

    const imgElement = document.createElement('img');
    imgElement.src = imageUrl;
    imgElement.alt = "Image Tag";
    imageThumbnail.appendChild(imgElement);

    imageTagThumbnails.appendChild(imageThumbnail);
    imageThumbnail.addEventListener('click', function() {
        removeImageTag(imageUrl);
    });
}

function removeImageTag(imageUrl) {
const index = imageTags.indexOf(imageUrl);
if (index !== -1) {
    imageTags.splice(index, 1);
    updateImageTagThumbnails();
}
}

function updateImageTagThumbnails() {
imageTagThumbnails.innerHTML = '';
imageTags.forEach(imageUrl => {
    const imageThumbnail = document.createElement('div');
    imageThumbnail.classList.add('image-tag-thumbnail');

    const imgElement = document.createElement('img');
    imgElement.src = imageUrl;
    imgElement.alt = "Image Tag";
    imageThumbnail.appendChild(imgElement);

    imageTagThumbnails.appendChild(imageThumbnail);
    imageThumbnail.addEventListener('click', function() {
        removeImageTag(imageUrl);
    });
});
}

function updateHiddenImageInput() {
    const imageTagsInput = document.querySelector('input[name="imageTags"]');
    imageTagsInput.value = imageTags.join(',');
}

const imageTagForm = document.getElementById('imageTagForm');
imageTagForm.addEventListener('submit', function(event) {
    updateHiddenImageInput();
    // let dropzoneInstance = Dropzone.forElement("#imageTagForm");

    // if (dropzoneInstance.getQueuedFiles().length > 0) {
    //     dropzoneInstance.processQueue();
    // }
    imageTagForm.submit();
});

var isGenerateStockImagesClicked = false;
var generateStockImagesButton = document.getElementById('generateStockImages');
generateStockImagesButton.addEventListener('click', function() {
    isGenerateStockImagesClicked = true;
    document.getElementById('isGenerateStockImagesClickedField').value = 'true';
    updateHiddenImageInput();
    showSpinner();
    imageTagForm.submit();
});

var imageTagFormSubmit = document.getElementById('imageTagFormSubmit');
imageTagFormSubmit.addEventListener('click', function() {
    updateHiddenImageInput();
    // let dropzoneInstance = Dropzone.forElement("#imageTagForm");

    // if (dropzoneInstance.getQueuedFiles().length > 0) {
    //     dropzoneInstance.processQueue(); 
    // }
    imageTagForm.submit();
});

updateImageTagThumbnails();
