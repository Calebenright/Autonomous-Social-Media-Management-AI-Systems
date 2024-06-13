function nextSlide(slideNumber) {
    const slides = document.querySelector('.slides');
    if (slides) {
      slides.style.transform = `translateX(-${(slideNumber - 1) * 100}%)`;
  }
}

function previousSlide(slideNumber) {
    const slides = document.querySelector('.slides');
    if (slides) {
      slides.style.transform = `translateX(-${(slideNumber - 1) * 100}%)`;
  }
}

function submitForm() {
    document.getElementById('feadlForm').submit(); // This will submit the form
}

document.addEventListener('DOMContentLoaded', function() {
    const slides = document.querySelector('.slides');
    if (slides) {
      slides.style.transform = 'translateX(0%)';
    }
});

function selectImage(imageId) {
    var images = document.getElementsByClassName('select-image');
    for (var i = 0; i < images.length; i++) {
        images[i].classList.remove('image-selected');
    }
    document.getElementById(imageId).classList.add('image-selected');
    document.getElementById('selectedImage').value = imageId; // Set the value of hidden input
}

function selectPlan(planId) {
    var plans = document.getElementsByClassName('select-plan');
    for (var i = 0; i < plans.length; i++) {
        plans[i].classList.remove('image-selected');
    }
    document.getElementById(planId).classList.add('image-selected');
    document.getElementById('selectedPlan').value = planId; // Set the value of hidden input
}

document.addEventListener('DOMContentLoaded', function() {
    const steps = ['step1-progress', 'step2-progress', 'step3-progress'];
    let currentStep = 0;
  
    function nextStep() {
      if (currentStep < steps.length) {
        const progressBar = document.getElementById(steps[currentStep]);
        progressBar.classList.add('active');
        currentStep++;
      }
    }
  
    // Simulate step completion
    document.querySelectorAll('.button').forEach(button => {
      button.addEventListener('click', nextStep);
    });
  });

  function closeMessage(element) {
    element.parentElement.style.display = 'none'; // Hide the message
    const messageId = element.parentElement.getAttribute('data-message-id');
    
    // Store the closed message ID in local storage
    const closedMessages = JSON.parse(localStorage.getItem('closed_messages')) || [];
    closedMessages.push(messageId);
    localStorage.setItem('closed_messages', JSON.stringify(closedMessages));
  }