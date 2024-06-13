

// INSTAGRAM //

function closeMessage(element) {
element.parentElement.style.display = 'none';
const messageId = element.parentElement.getAttribute('data-message-id');

const closedMessages = JSON.parse(localStorage.getItem('closed_messages')) || [];
closedMessages.push(messageId);
localStorage.setItem('closed_messages', JSON.stringify(closedMessages));
}

document.addEventListener("DOMContentLoaded", function() {
    var progressBar = document.getElementById('progressBar');
    setTimeout(() => {
        progressBar.style.width = "75%";
    }, 1000); // Start the animation 1 second after page loads
});

function nextSlide(slideNumber) {
    const slides = document.querySelector('.slides');
    slides.style.transform = 'translateX(-' + (slideNumber - 1) * 100 + '%)';
}

function submitForm() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    // Process the submission, e.g., using Fetch API or form submission
    console.log('Submitting:', name, email);
    alert('Form submitted! Check console for details.');
}