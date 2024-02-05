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

function loadMedia(nextMedia) {
    var loadedImage = document.getElementById('loaded-image');
    var loadedVideo = document.getElementById('loaded-video');
    var videoSource = document.getElementById('video-source');

    if (nextMedia.endsWith('.mp4') || nextMedia.endsWith('.avi') || nextMedia.endsWith('.mov')) {
        loadedImage.style.display = 'none'; // Hide the image element
        videoSource.src = nextMedia;        // Set the video source
        loadedVideo.load();                 // Load the video
        loadedVideo.style.display = 'block';// Show the video element
    } else {
        loadedVideo.style.display = 'none'; // Hide the video element
        loadedImage.src = nextMedia;        // Set the image source
        loadedImage.style.display = 'block';// Show the image element
    }
}

function getCookie(name) {
    const cookieValue = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return cookieValue ? cookieValue.pop() : '';
}
var csrfToken = getCookie('csrftoken');

function addGraphics(imageUrl) {
    $.ajax({
        url: '/add_graphics/', 
        type: 'post',
        headers: {
            'X-CSRFToken': csrfToken 
        },
        dataType: 'json',
        data: {
            'image_url': imageUrl
        },
        success: function (data) {
            console.log('addGraphics ran')
        },
        error: function(error) {
            loadedImage.src = 'https://storage.googleapis.com/starter_web_app_bucket/assets/error.png';
            document.getElementById('generatePostButton').disabled = false;
            displayErrorMessage(error.message)
        }
    });
}

const tagInput = document.getElementById('tagInput');
const tagBubbles = document.getElementById('tagBubbles');
const tags = tagsArray;
const randomTag = tags[Math.floor(Math.random() * tags.length)];

document.addEventListener('DOMContentLoaded', () => {

    let previousProgress = null;
    document.getElementById('generatePostButton').disabled = true;

    const unsubscribe = onSnapshot(statusDocRef, (docSnapshot) => {
        if (docSnapshot.exists()) {
            const { progress, next_image_url: nextImage } = docSnapshot.data();

            // Only proceed if progress has changed
            if (progress !== previousProgress) {
                console.log('snapped');
                console.log('progress: ', progress);

                if (progress === 90) {
                    console.log('run progress graphic');
                    addGraphics(nextImage);
                }

                if (progress === 100) {
                    document.getElementById('generatePostButton').disabled = false;
                    if (loadedImage) {
                        loadMedia(nextImage);
                    }
                    if (dynamicUrl) {
                        dynamicUrl.value = nextImage;
                    }
                }

                // Update previousProgress with the current progress
                previousProgress = progress;
            }
        }
    }, (error) => {
        console.error('Error in realtime listener:', error);
    });

});

document.addEventListener('DOMContentLoaded', () => {
    getDoc(statusDocRef).then((doc) => {
        if (doc.exists()) {
            const progress = doc.data().progress;
            if (progress === 95) {
                const nextImage = doc.data().next_image_url;
                console.log('Running addGraphics with:', nextImage);
                addGraphics(nextImage);
            }
        } else {
            console.log('No such document!');
        }
    }).catch((error) => {
        console.log('Error getting document:', error);
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const thumbnails = document.querySelectorAll('.post-type-thumbnail');

    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', () => {
            thumbnails.forEach(thumb => thumb.classList.remove('selected'));
            thumbnail.classList.add('selected');
            const selectedValue = thumbnail.getAttribute('data-value');

            const photoCard = document.getElementById("photo-none");
            const keywordCard = document.getElementById("keyword-none");
            const adDescNone = document.getElementById("ad-desc-none");
            const thumbnailCard = document.getElementById("thumbnail-none");
            const fileCard = document.getElementById("file-none");

            if (selectedValue == "text") {
                fileCard.style.display = 'none';
                photoCard.style.display = 'none';
                keywordCard.style.display = 'none';
                adDescNone.style.display = 'none';
                thumbnailCard.style.display = 'none';
            } else if (selectedValue == "photo") {
                fileCard.style.display = 'none';
                photoCard.style.display = 'block';
                keywordCard.style.display = 'none';
                adDescNone.style.display = 'none';
                thumbnailCard.style.display = 'block';
            } else if (selectedValue == "graphic") {
                fileCard.style.display = 'none';
                photoCard.style.display = 'none';
                keywordCard.style.display = 'block';
                adDescNone.style.display = 'none';
                thumbnailCard.style.display = 'block';
            } else if (selectedValue == "ad") {
                fileCard.style.display = 'none';
                photoCard.style.display = 'none';
                keywordCard.style.display = 'none';
                adDescNone.style.display = 'block';
                thumbnailCard.style.display = 'block';
            } else if (selectedValue == "up") {
                fileCard.style.display = 'block';
                photoCard.style.display = 'none';
                keywordCard.style.display = 'none';
                adDescNone.style.display = 'none';
                thumbnailCard.style.display = 'none';
            }

            const aiDescription = document.querySelector('input[name="ai-description"]');
            if (aiDescription) {
                aiDescription.value = randomTag;
            }

            const adDescription = document.querySelector('input[name="ad-description"]');
            if (adDescription) {
                adDescription.value = jsonDump.businessDescription;
            }
        });
    });

    const defaultThumbnail = document.querySelector('.post-type-thumbnail.selected');
    if (defaultThumbnail) {
        defaultThumbnail.click();
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
    var closeButton = document.createElement('span');
    closeButton.className = 'closebtn';
    closeButton.innerHTML = '&times;';
    closeButton.onclick = function() { closeMessage(this); };
    errorMessageLi.appendChild(closeButton);
    errorMessagesContainer.querySelector('.messages').appendChild(errorMessageLi);
}


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


// ----------------- POST TYPE ----------------- //
