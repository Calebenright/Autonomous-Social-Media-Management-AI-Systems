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
const loadedImage = document.getElementById('loaded-image');
var dynamicUrl = document.getElementById('dynamicUrl')

onAuthStateChanged(auth, (user) => {
    if (user) {} else {
        window.location.href = '/login/';
    }
});

document.addEventListener('DOMContentLoaded', () => {
    let previousProgress = 0;
    let progressHasStarted = false;
    const submitButton = document.getElementById('submit-button');
    const formContainer = document.getElementById('form-container');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.querySelector('.progress-bar');

    if (submitButton) {
        submitButton.disabled = true; // Disable submit button until progress is 100%
    }

    const unsubscribe = onSnapshot(statusDocRef, (docSnapshot) => {
        if (docSnapshot.exists()) {
            const { clip_percent: clipPercent } = docSnapshot.data();

            if (clipPercent !== undefined) {
                if (clipPercent !== previousProgress) {
                    console.log('Firestore update received');
                    console.log('Clip Percent: ', clipPercent);
                    progressHasStarted = true; // Update flag when progress changes

                    // Update progress bar
                    if (progressBar) {
                        progressBar.style.width = `${clipPercent}%`;
                        progressBar.setAttribute('aria-valuenow', clipPercent);
                    }

                    // Conditionally show form or progress bar based on clip_percent
                    if (clipPercent >= 100) {
                        if (formContainer) formContainer.style.display = 'block';
                        if (progressContainer) progressContainer.style.display = 'none';
                        if (submitButton) submitButton.disabled = false; // Enable the submit button
                    } else {
                        if (formContainer) formContainer.style.display = 'none';
                        if (progressContainer) progressContainer.style.display = 'block';
                    }

                    previousProgress = clipPercent;
                }
            } else {
                // Do nothing if clip_percent is not present
                console.log('clip_percent not found in document.');
            }
        }
    }, (error) => {
        console.error('Error in Firestore listener:', error);
        displayError(); // Call the error handler
    });

    // Fallback in case progress does not update
    setTimeout(() => {
        if (!progressHasStarted) {
            console.error('Progress stuck at 0.');
            displayError('An unknown error occurred. Please try again.');
        }
    }, 50000);

    // Error handler function
    function displayError(errorMessage = 'An unknown error occurred. Please try again.') {
        if (submitButton) {
            submitButton.disabled = false;
        }
        displayErrorMessage(errorMessage); // Assuming displayErrorMessage is defined elsewhere
    }
});

function displayErrorMessage(errorMsg) {
    var errorMessagesContainer = document.getElementById('error-messages-container');
    if (errorMessagesContainer.querySelectorAll('.messages').length === 0) {
        var messagesUl = document.createElement('ul');
        messagesUl.className = 'messages';
        errorMessagesContainer.appendChild(messagesUl);
    }
    var errorMessageLi = document.createElement('li');
    errorMessageLi.className = 'danger';
    errorMessageLi.setAttribute('data-message-id', 'ajaxError');
    var textNode = document.createTextNode(errorMsg); // Create text node with error message
    errorMessageLi.appendChild(textNode); // Append the text node to the li element
    var closeButton = document.createElement('span');
    closeButton.className = 'closebtn';
    closeButton.innerHTML = '&times;';
    closeButton.onclick = function() { this.parentElement.style.display = 'none'; }; // Corrected to hide the parent li element
    errorMessageLi.appendChild(closeButton);
    errorMessagesContainer.querySelector('.messages').appendChild(errorMessageLi);
}


// ----------------- POST TYPE ----------------- //
