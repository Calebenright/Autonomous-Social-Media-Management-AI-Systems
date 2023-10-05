document.addEventListener('DOMContentLoaded', () => {
    const radioButtons = document.querySelectorAll('input[name="flexRadioDefault"]');
    const contentCards = document.querySelectorAll('.content-card');

    radioButtons.forEach(radioButton => {
        radioButton.addEventListener('change', () => {
            const selectedValue = radioButton.value;
            
            contentCards.forEach(card => {
                card.style.display = 'none';
            });

            const correspondingCard = document.getElementById(`content-card-${selectedValue}`);
            if (correspondingCard) {
                correspondingCard.style.display = 'block';
            }
        });

        if (radioButton.checked) {
            radioButton.dispatchEvent(new Event('change'));
        }
    });

    
});

const tagInput = document.getElementById('tagInput');
const tagBubbles = document.getElementById('tagBubbles');
const tags = tagsArray;

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