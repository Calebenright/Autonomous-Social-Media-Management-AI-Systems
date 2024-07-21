"use strict";

var overlayContainer = document.getElementById('ftueOverlay');
var ftueFormContainer = document.getElementById('ftueFormContainer');
const animatedCharacter = document.getElementById('animatedCharacter');
let currentAnimationIndex = 0;
let isLoading = false;
const animationPause = 2;

function showSpinner() {
    var loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.style.display = 'flex';
}

function showPreload() {
    var loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.style.display = 'flex';
}

function hidePreload() {
    var loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.style.display = 'none';
}


animatedCharacter.addEventListener('click', function() {
    if (!isLoading) {
        isLoading = true;

        if (currentAnimationIndex < animationPause) {
            const newImage = new Image();
            newImage.onload = function() {
                animatedCharacter.src = newImage.src;
                isLoading = false; 
            };
            currentAnimationIndex = (currentAnimationIndex + 1) % animationGifPaths.length;
            newImage.src = animationGifPaths[currentAnimationIndex];
            
        } else if (currentAnimationIndex == animationPause) {
            animatedCharacter.style.display = 'none';
            var ftueTour = document.querySelector('.tour-ftue');
            if (ftueTour) {
                ftueTour.classList.remove('hide');
              }
            overlayContainer.style.display = 'none';
        } else if (currentAnimationIndex < animationGifPaths.length-1) {
            const newImage = new Image();
            newImage.onload = function() {
                animatedCharacter.src = newImage.src;
                isLoading = false; 
            };
            currentAnimationIndex = (currentAnimationIndex + 1) % animationGifPaths.length;
            newImage.src = animationGifPaths[currentAnimationIndex];
            
        } else {
            // ftueFormContainer.style.display = 'block';
            animatedCharacter.style.display = 'none';
            ftueFormContainer.submit();
            showSpinner();
        }
        
    }
});

function preloadImages() {
    const preloadImage = new Image();
    preloadImage.onload = function() {
        animatedCharacter.src = animationGifPaths[currentAnimationIndex];

        var ftueTour = document.querySelector('.tour-ftue');
        if (ftueTour) {
            ftueTour.classList.add('hide');
        }

        console.log('preload done');
    };

    preloadImage.src = animationGifPaths[currentAnimationIndex];
    hidePreload();

};

showPreload();
preloadImages();

window.onload = function() {
    ftue();
};

function ftue() {
    overlayContainer.style.display = 'flex';
}

function tourDone() {
    const newImage = new Image();
    currentAnimationIndex = (currentAnimationIndex + 1) % animationGifPaths.length;
    newImage.src = animationGifPaths[currentAnimationIndex];
    newImage.onload = function() {
        animatedCharacter.src = newImage.src;
        console.log('pause');
        overlayContainer.style.display = 'flex';
        animatedCharacter.style.display = 'block';
    };
    isLoading = false; 
    console.log(currentAnimationIndex);
}