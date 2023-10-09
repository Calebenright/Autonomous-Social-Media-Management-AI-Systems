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

const isEndFtueEnabled = userSettings.endFtue === true;
const autoState = userSettings.autoState;
const isFtueEnabled = userSettings.ftue === true;
const isFtue2Enabled = userSettings.ftue2 === true;
const isFtue3Enabled = userSettings.ftue3 === true;
const isFtue4Enabled = userSettings.ftue4 === true;

// Check if autoState is equal to 1
const isAutoState1 = autoState === 1;
const isAutoState2 = autoState === 2;
const isAutoState3 = autoState === 3;

console.log(isFtueEnabled);
console.log(isFtue2Enabled);
console.log(isFtue3Enabled);
console.log(isFtue4Enabled);

if (isEndFtueEnabled){
    const firebaseApp = initializeApp(firebaseConfig);
    const db = getFirestore(firebaseApp);
    const statusDocRef = doc(collection(db, 'users'), jsonDump.userId);
    
    console.log(autoState);

    if (isAutoState2){
        const progress = document.getElementById('progress');
        const progressBar = document.getElementById('progress-bar');
        const progress2 = document.getElementById('progress2');
        const progressBar2 = document.getElementById('progress-bar2');
        const progress3 = document.getElementById('progress3');
        const progressBar3 = document.getElementById('progress-bar3');
        const imageContainer = document.getElementById('image-container');
        const loadingGif = document.getElementById('loading-gif');
        const loadDone = document.getElementById('load-done');
        const loadStart = document.getElementById('load-start');
        const resetButton = document.getElementById('resetButton');
        loadStart.style.display = 'block';
        

        const unsubscribe = onSnapshot(statusDocRef, (docSnapshot) => {
            if (docSnapshot.exists()) {
                const status = docSnapshot.data().status;
                const status2 = docSnapshot.data().status2;
                const status3 = docSnapshot.data().status3;
                let totalPercentageIncrease = 0;

                if (status === '100') {
                    totalPercentageIncrease += 4;
                }
                
                if (status2 === '100') {
                    totalPercentageIncrease += 55;
                }
                
                if (status3 === '100') {
                    totalPercentageIncrease += 30;
                }
                
                progress.style.width = `${totalPercentageIncrease}%`;
                
                
                
                if (status === '100' && status2 === '100' && status3 === '100') {
                    loadDone.style.display = 'block';
                    loadingGif.src = gifDone;
                    progressBar.style.display = 'none';
                    resetButton.style.display = 'none';
                }
                else {
                    loadDone.style.display = 'none';
                    loadingGif.src = gifStart;
                    progressBar.style.display = 'block';
                    resetButton.style.display = 'block';
                }
            }
        }, (error) => {
            console.error('Error in realtime listener:', error);
        });
    }

    // To stop listening to changes (e.g., when you no longer need the listener):
    // unsubscribe();
}

// FTUE CONTROLLER //

if (isFtueEnabled || isFtue2Enabled || isFtue3Enabled || isFtue4Enabled) {
    function ftue() {
        var overlayContainer = document.getElementById('overlayContainer');
        var submitButton = document.querySelector('#myForm button[type="submit"]');
        overlayContainer.style.display = 'flex';
        submitButton.disabled = true;
    }

    var ftueFormContainer = document.getElementById('ftueFormContainer');
    var ftueFormContainer2 = document.getElementById('ftueFormContainer2');
    var ftueFormContainer3 = document.getElementById('ftueFormContainer3');
    const animatedCharacter = document.getElementById('animatedCharacter');
    const animatedCharacter2 = document.getElementById('animatedCharacter2');
    const animatedCharacter3 = document.getElementById('animatedCharacter3');
    const animatedCharacter4 = document.getElementById('animatedCharacter4');

    let currentAnimationIndex = 0;
    let isLoading = false;

    if (isFtueEnabled) {
        animatedCharacter.addEventListener('click', function() {
            if (!isLoading) {
                isLoading = true;

                if (currentAnimationIndex < animationGifPaths.length - 1) {
                    const newImage = new Image();
                    newImage.onload = function() {
                        animatedCharacter.src = newImage.src;
                        isLoading = false; 
                    };
                    currentAnimationIndex = (currentAnimationIndex + 1) % animationGifPaths.length;
                    newImage.src = animationGifPaths[currentAnimationIndex];
                } else {

                    const elementsToDisable = document.querySelectorAll('a');
                    elementsToDisable.forEach(element => {
                        element.disabled = true;
                    });
                    
                    ftueFormContainer.style.display = 'block';
                    var character = document.getElementById('animatedCharacter');
                    character.style.display = 'none';
                }
            }
        });
        const preloadImages = () => {
        const preloadImage = new Image();
        preloadImage.onload = function() {
            animatedCharacter.src = animationGifPaths[currentAnimationIndex];
            ftueFormContainer.style.display = 'none';
        };
        preloadImage.src = animationGifPaths[currentAnimationIndex];
        };

        window.addEventListener('load', preloadImages);
    } else if (isFtue2Enabled) {
        animatedCharacter2.addEventListener('click', function() {
            if (!isLoading) {
                isLoading = true;

                if (currentAnimationIndex < animationGifPaths2.length - 1) {
                    const newImage = new Image();
                    newImage.onload = function() {
                        animatedCharacter2.src = newImage.src;
                        isLoading = false;
                    };
                    currentAnimationIndex = (currentAnimationIndex + 1) % animationGifPaths2.length;
                    newImage.src = animationGifPaths2[currentAnimationIndex];
                } else {
                    var overlayContainer = document.getElementById('overlayContainer');
                    overlayContainer.style.display = 'none';
                    const elementsToDisable = document.querySelectorAll('a');
                    elementsToDisable.forEach(element => {
                        element.disabled = true;
                    });
                }
            }
        });
        const preloadImages = () => {
        const preloadImage = new Image();
        preloadImage.onload = function() {
            animatedCharacter2.src = animationGifPaths2[currentAnimationIndex];
        };
        preloadImage.src = animationGifPaths2[currentAnimationIndex];
        };

        window.addEventListener('load', preloadImages);
    } else if (isFtue3Enabled) {
        animatedCharacter3.addEventListener('click', function() {
            if (!isLoading) {
                isLoading = true;

                if (currentAnimationIndex < animationGifPaths3.length - 1) {

                    const newImage = new Image();
                    newImage.onload = function() {
                        animatedCharacter3.src = newImage.src;
                        isLoading = false; 
                    };
                    currentAnimationIndex = (currentAnimationIndex + 1) % animationGifPaths3.length;
                    newImage.src = animationGifPaths3[currentAnimationIndex];
                } else {
                    ftueFormContainer.style.display = 'block';
                    var character = document.getElementById('animatedCharacter3');
                    character.style.display = 'none';
                }
                
            }
        });
        const preloadImages = () => {
        const preloadImage = new Image();
        preloadImage.onload = function() {
            animatedCharacter3.src = animationGifPaths3[currentAnimationIndex];
            ftueFormContainer.style.display = 'none';

        };
        preloadImage.src = animationGifPaths3[currentAnimationIndex];
        };

        window.addEventListener('load', preloadImages);
    } else if (isFtue4Enabled) {
        animatedCharacter4.addEventListener('click', function() {
            if (!isLoading) {
                isLoading = true;

                if (currentAnimationIndex < animationGifPaths4.length - 1) {
                    const newImage = new Image();
                    newImage.onload = function() {
                        animatedCharacter4.src = newImage.src;
                        isLoading = false;
                    };
                    currentAnimationIndex = (currentAnimationIndex + 1) % animationGifPaths4.length;
                    newImage.src = animationGifPaths4[currentAnimationIndex];
                } else {

                    const elementsToDisable = document.querySelectorAll('a');
                    elementsToDisable.forEach(element => {
                        element.disabled = true;
                    });
                    ftueFormContainer2.style.display = 'block';
                    ftueFormContainer3.style.display = 'block';
                    var character = document.getElementById('animatedCharacter4');
                    character.style.display = 'none';
                }
            }
        });
        const preloadImages = () => {
        const preloadImage = new Image();
        preloadImage.onload = function() {
            animatedCharacter4.src = animationGifPaths4[currentAnimationIndex];
            ftueFormContainer2.style.display = 'none';
            ftueFormContainer3.style.display = 'none';
        };
        preloadImage.src = animationGifPaths4[currentAnimationIndex];
        };

        window.addEventListener('load', preloadImages);
    }

    window.onload = function() {
        ftue();
    };

}
