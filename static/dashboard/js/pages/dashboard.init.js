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

document.addEventListener('DOMContentLoaded', function () {
    const firstHandle = document.getElementById('firstHandle');
    const secondHandle = document.getElementById('secondHandle');
    const textWeight = document.getElementById('textWeight');
    const stockWeight = document.getElementById('stockWeight');
    const graphicWeight = document.getElementById('graphicWeight');

    function updateWeights() {
        const firstValue = parseInt(firstHandle.value);
        const secondValue = parseInt(secondHandle.value);
        const textPostWeight = firstValue;
        const stockPostWeight = secondValue - firstValue;
        const graphicPostWeight = 100 - secondValue;

        textWeight.textContent = textPostWeight;
        stockWeight.textContent = stockPostWeight;
        graphicWeight.textContent = graphicPostWeight;
    }

    firstHandle.addEventListener('input', function() {
        if (parseInt(firstHandle.value) > parseInt(secondHandle.value)) {
            firstHandle.value = secondHandle.value;
        }
        updateWeights();
    });

    secondHandle.addEventListener('input', function() {
        if (parseInt(secondHandle.value) < parseInt(firstHandle.value)) {
            secondHandle.value = firstHandle.value;
        }
        updateWeights();
    });

    // Set initial values based on data attributes
    firstHandle.value = firstHandle.dataset.textWeight;
    secondHandle.value = secondHandle.dataset.stockWeight;

    updateWeights();  // Call once on load to set initial positions
});

document.addEventListener('DOMContentLoaded', function () {
    const firstHandle = document.getElementById('firstHandle');
    const secondHandle = document.getElementById('secondHandle');
    const colorDisplay = document.getElementById('colorDisplay');

    function updateBackground() {
        const firstValue = parseInt(firstHandle.value);
        const secondValue = parseInt(secondHandle.value);
        const thirdValue = 100 - secondValue;

        // Assume each range controls a different color channel
        colorDisplay.style.background = `linear-gradient(to right, 
            #B1C74C 0%, #B1C74C ${firstValue}%, 
            #2c3a8a ${firstValue}%, #2c3a8a ${secondValue}%, 
            #18225e ${secondValue}%, #18225e 100%)`;
    }

    firstHandle.addEventListener('input', updateBackground);
    secondHandle.addEventListener('input', updateBackground);

    updateBackground(); // Set initial background on load
});

