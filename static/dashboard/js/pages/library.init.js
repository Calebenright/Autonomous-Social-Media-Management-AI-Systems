"use strict";

// FIREBASE LISTENER //

import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-app.js';
import { getFirestore, collection, doc, setDoc, getDoc, onSnapshot } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-firestore.js';
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
const statusDocRef = doc(collection(db, 'users'), jsonDump.userId);

onAuthStateChanged(auth, (user) => {
    if (user) {} else {
        window.location.href = '/login/';
    }
});

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

// -------------------- IMAGE TAGS ------------------------ //

const imageTagThumbnails = document.getElementById('imageTagThumbnails');
const imageTags = imageTagsArray;

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

        // Create img element for displaying the image
        const imgElement = document.createElement('img');
        imgElement.src = imageUrl;
        imgElement.alt = "Image Tag";
        imageThumbnail.appendChild(imgElement);

        // Create a remove button
        const removeBtn = document.createElement('button');
        removeBtn.innerHTML = 'X';
        removeBtn.classList.add('remove-btn');
        removeBtn.onclick = function(event) {
            event.stopPropagation(); // Prevent triggering the thumbnail's click
            removeImageTag(imageUrl);
        };
        imageThumbnail.appendChild(removeBtn);

        // Create a download link
        const downloadLink = document.createElement('a');
        downloadLink.href = imageUrl;
        downloadLink.download = imageUrl.split('/').pop(); // Suggest filename from URL
        downloadLink.innerHTML = 'Download';
        downloadLink.classList.add('download-link');
        imageThumbnail.appendChild(downloadLink);

        imageTagThumbnails.appendChild(imageThumbnail);

        // Create overlay div
        const overlay = document.createElement('div');
        overlay.classList.add('overlay');

        // Append children (download and remove actions) to overlay
        overlay.appendChild(removeBtn);
        overlay.appendChild(downloadLink);

        // Append overlay to imageThumbnail
        imageThumbnail.appendChild(overlay);
    });
}

function updateHiddenImageInput() {
    const imageTagsInput = document.querySelector('input[name="imageTags"]');
    imageTagsInput.value = imageTags.join(',');
}

const imageTagForm = document.getElementById('imageTagForm');
imageTagForm.addEventListener('submit', function(event) {
    updateHiddenImageInput();
    imageTagForm.submit();
});

var isGenerateStockImagesClicked = false;
var generateStockImagesButton = document.getElementById('generateStockImages');
if (generateStockImagesButton) {
    generateStockImagesButton.addEventListener('click', function() {
        isGenerateStockImagesClicked = true;
        document.getElementById('isGenerateStockImagesClickedField').value = 'true';
        updateHiddenImageInput();
        showSpinner();
        imageTagForm.submit();
    });
}

var imageTagFormSubmit = document.getElementById('imageTagFormSubmit');
imageTagFormSubmit.addEventListener('click', function() {
    updateHiddenImageInput();
    imageTagForm.submit();
});

updateImageTagThumbnails();
