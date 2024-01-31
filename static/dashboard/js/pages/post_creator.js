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
    if (user) {
        console.log('User is signed in.');
    } else {
        window.location.href = '/login/';
    }
});

const unsubscribe = onSnapshot(statusDocRef, (docSnapshot) => {
    if (docSnapshot.exists()) {
        const progress = docSnapshot.data().progress;
        const nextImage = docSnapshot.data().next_image_url;

        if (progress === 90) {
            addGraphics(nextImage)
        }

        if (progress === 100) {
            if (loadedImage) {
                loadMedia(nextImage);
            }
            if (dynamicUrl) {
                dynamicUrl.value = nextImage;
            }
        }
    }
}, (error) => {
    console.error('Error in realtime listener:', error);
});

function loadMedia(nextMedia) {
    var loadedImage = document.getElementById('loaded-image');
    var loadedVideo = document.getElementById('loaded-video');
    var videoSource = document.getElementById('video-source');

    // Check if the media is a video by its extension
    if (nextMedia.endsWith('.mp4') || nextMedia.endsWith('.avi') || nextMedia.endsWith('.mov')) {
        // It's a video
        loadedImage.style.display = 'none'; // Hide the image element
        videoSource.src = nextMedia;        // Set the video source
        loadedVideo.load();                 // Load the video
        loadedVideo.style.display = 'block';// Show the video element
    } else {
        // It's an image
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
            console.log('Success:', data)
        },
        error: function(error) {
            console.log('Error:', error)
            loadedImage.src = 'https://storage.googleapis.com/starter_web_app_bucket/assets/error.png';
            if (error.status == 400 && error.responseJSON && error.responseJSON.error) {
                console.log('Error:', error.responseJSON.error);
                var $errorMessagesContainer = $('#error-messages-container');
                if ($errorMessagesContainer.find('.messages').length === 0) {
                    $errorMessagesContainer.append('<ul class="messages"></ul>');
                }
                var errorMessage = '<li class="danger" data-message-id="ajaxError">' + error.responseJSON.error +
                    '<span class="closebtn" onclick="closeMessage(this);">&times;</span></li>';
                $errorMessagesContainer.find('.messages').append(errorMessage);
            }
        }
    });
}

const tagInput = document.getElementById('tagInput');
const tagBubbles = document.getElementById('tagBubbles');
const tags = tagsArray;
const randomTag = tags[Math.floor(Math.random() * tags.length)];

document.addEventListener('DOMContentLoaded', () => {
    const thumbnails = document.querySelectorAll('.post-type-thumbnail');
    const contentCards = document.querySelectorAll('.content-card');
    const stockDescription = document.querySelector('input[name="stock-description"]');
    const graphicDescription = document.querySelector('input[name="graphic-description"]');
    const adDescription = document.querySelector('input[name="ad-creative-description"]');

    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', () => {
            thumbnails.forEach(thumb => thumb.classList.remove('selected'));
            thumbnail.classList.add('selected');
            const selectedValue = thumbnail.getAttribute('data-value');
            contentCards.forEach(card => {
                card.style.display = 'none';
            });

            const correspondingCard = document.getElementById(`content-card-${selectedValue}`);
            if (correspondingCard) {
                if (selectedValue == "stock") {
                    stockDescription.value = randomTag;
                } else if (selectedValue == "graphic") {
                    graphicDescription.value = randomTag;
                } else if (selectedValue == "ad") {
                    adDescription.value = randomTag;
                }
                correspondingCard.style.display = 'block';
            }
        });

    });

    const defaultThumbnail = document.querySelector('.post-type-thumbnail.selected');
    if (defaultThumbnail) {
        defaultThumbnail.click();
    }

});

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
