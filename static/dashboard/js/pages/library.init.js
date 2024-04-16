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

let currentPage = 1;
const imagesPerPage = 30;
const imageTags = imageTagsArray;
let totalImages = imageTags.length; // Should be declared with 'let' if it needs to be updated

function removeImageTag(imageUrl) {
    const index = imageTags.indexOf(imageUrl);
    if (index !== -1) {
        imageTags.splice(index, 1);
        updateTotalImagesAndThumbnails();
    }
}

function updateTotalImagesAndThumbnails() {
    totalImages = imageTags.length; // Update totalImages based on the current number of image tags
    updateImageTagThumbnails(); // Then update the thumbnails displayed
    updatePaginationControls(); // And also update the pagination controls accordingly
}

function updateImageTagThumbnails() {
    const startIndex = (currentPage - 1) * imagesPerPage;
    const endIndex = startIndex + imagesPerPage;
    const paginatedImageUrls = imageTags.slice(startIndex, endIndex); // Get images for the current page

    const imageTagThumbnails = document.getElementById("imageTagThumbnails");
    imageTagThumbnails.innerHTML = ''; // Clear existing thumbnails

    paginatedImageUrls.forEach(imageUrl => {
        const imageThumbnail = document.createElement('div');
        imageThumbnail.classList.add('image-tag-thumbnail');

        const imgElement = document.createElement('img');
        imgElement.src = imageUrl;
        imgElement.alt = "Image Tag";
        imageThumbnail.appendChild(imgElement);

        // Overlay div
        const overlay = document.createElement('div');
        overlay.classList.add('overlay');

        // Create a remove button
        const removeBtn = document.createElement('button');
        removeBtn.innerHTML = 'X';
        removeBtn.classList.add('remove-btn');
        removeBtn.onclick = function(event) {
            event.preventDefault();
            removeImageTag(imageUrl);
        };
        overlay.appendChild(removeBtn); // Append removeBtn to overlay instead of imageThumbnail

        // Create a download link
        const downloadLink = document.createElement('a');
        downloadLink.href = imageUrl;
        downloadLink.download = imageUrl.split('/').pop(); // Suggest filename from URL
        downloadLink.innerHTML = 'Download';
        downloadLink.classList.add('download-link');
        overlay.appendChild(downloadLink); // Append downloadLink to overlay instead of imageThumbnail

        // Append overlay to imageThumbnail
        imageThumbnail.appendChild(overlay);

        imageTagThumbnails.appendChild(imageThumbnail);
    });

    updatePaginationControls(); // Call to update pagination controls based on current state
}

function updatePaginationControls() {
    const container = document.getElementById('pagination-controls');
    container.innerHTML = '';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';

    const buttonContainer = document.createElement('div');
    buttonContainer.style.display = 'flex';
    buttonContainer.style.justifyContent = 'space-between';
    buttonContainer.style.marginBottom = '10px';

    const totalPages = Math.ceil(totalImages / imagesPerPage);

    // Previous Button
    if (currentPage > 1) {
        const prevButton = document.createElement('button');
        prevButton.textContent = 'Previous';
        prevButton.className = 'pagination-button prev-button';
        prevButton.type = 'button';
        prevButton.onclick = function() {
            if (currentPage > 1) {
                currentPage--;
                updateImageTagThumbnails(); // Refresh thumbnails to show the previous page
            }
        };
        buttonContainer.appendChild(prevButton);
    }

    // Next Button
    if (currentPage < totalPages) {
        const nextButton = document.createElement('button');
        nextButton.textContent = 'Next';
        nextButton.className = 'pagination-button next-button';
        nextButton.type = 'button';
        nextButton.onclick = function() {
            if (currentPage < totalPages) {
                currentPage++;
                updateImageTagThumbnails(); // Refresh thumbnails to show the next page
            }
        };
        buttonContainer.appendChild(nextButton);
    }

    // Page Information Display
    container.appendChild(buttonContainer);
    const pageInfo = document.createElement('span');
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    pageInfo.className = 'page-info';
    container.appendChild(pageInfo);
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

var isGeneratePixabayImagesClicked = false;
var generatePixabayImagesButton = document.getElementById('generatePixabayImages');
if (generatePixabayImagesButton) {
    generatePixabayImagesButton.addEventListener('click', function() {
        isGeneratePixabayImagesClicked = true;
        document.getElementById('isGeneratePixabayImagesClickedField').value = 'true';
        updateHiddenImageInput();
        showSpinner();
        imageTagForm.submit();
    });
}

var imageTagFormSubmit = document.getElementById('imageTagFormSubmit');
imageTagFormSubmit.addEventListener('click', function() {
    showSpinner();
    updateHiddenImageInput();
    imageTagForm.submit();
});

updateImageTagThumbnails();
