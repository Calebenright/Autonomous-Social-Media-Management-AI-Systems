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
const loadedImage = document.getElementById('loaded-image');

const unsubscribe = onSnapshot(statusDocRef, (docSnapshot) => {
    if (docSnapshot.exists()) {
        console.log('exists')
        const progress = docSnapshot.data().progress;
        const nextImage = docSnapshot.data().next_image_url;

        console.log(progress)
        console.log(nextImage)

        if (progress === 90) {
            // if (jsonDump.selectedOption === 'graphic' || jsonDump.selectedOption === 'ad') {
            addGraphics(nextImage)
            // } else {
            //     statusDocRef.update({
            //         100: progress,
            //         next_image_url: nextImage
            //     })
            //     .then(() => {
            //         console.log("Document successfully updated!");
            //     })
            //     .catch((error) => {
            //         console.error("Error updating document: ", error);
            //     });
            //     if (loadedImage) {
            //         loadedImage.src = nextImage;
            //     }
            // }
        }

        if (progress === 100) {
            if (loadedImage) {
                loadedImage.src = nextImage;
            }
        }
    }
}, (error) => {
    console.error('Error in realtime listener:', error);
});

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

window.onload = function() {
    selectNoneAd();
    selectNone();
};