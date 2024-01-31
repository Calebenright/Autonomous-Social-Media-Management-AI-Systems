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
    if (user) {
        console.log('User is signed in.');
    } else {
        window.location.href = '/login/';
    }
});

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
    // let dropzoneInstance = Dropzone.forElement("#imageTagForm");

    // if (dropzoneInstance.getQueuedFiles().length > 0) {
    //     dropzoneInstance.processQueue(); 
    // }
    imageTagForm.submit();
});

updateImageTagThumbnails();
