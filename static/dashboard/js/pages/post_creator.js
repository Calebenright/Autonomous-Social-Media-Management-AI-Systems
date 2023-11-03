
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