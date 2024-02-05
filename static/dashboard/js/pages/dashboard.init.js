"use strict";

const isFtueEnabled = userSettings.ftue === true;

// FTUE CONTROLLER //

if (!isFtueEnabled) {
    function ftue() {
        var overlayContainer = document.getElementById('ftueOverlay');
        overlayContainer.style.display = 'flex';
    }

    var ftueFormContainer = document.getElementById('ftueFormContainer');
    const animatedCharacter = document.getElementById('animatedCharacter');

    let currentAnimationIndex = 0;
    let isLoading = false;

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

    window.onload = function() {
        ftue();
    };

}
