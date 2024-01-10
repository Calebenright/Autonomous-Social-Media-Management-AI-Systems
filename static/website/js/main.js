'use strict';

// Remove preload class once page is fully loaded

window.addEventListener('load', function() {
  Array.from(document.getElementsByTagName('body')).forEach(function(el) {
    el.classList.remove('preload');
  });
});

// Add class to navigation when scrolling down

document.addEventListener('scroll', function() {
  const header = document.querySelector('.header-main');
  if (window.scrollY >= 20) {
    header.classList.add('fade-in');
  } else {
    header.classList.remove('fade-in');
  }
});

Array.from(document.getElementsByClassName('nav-toggle')).forEach(function(el) {
  el.addEventListener('click', function() {
    Array.from(document.getElementsByTagName('body')).forEach(function(el) {
      el.classList.toggle('no-scroll');
    });
    Array.from(document.getElementsByClassName('header-main')).forEach(function(el) {
      el.classList.toggle('active');
    });
  });
});

document.addEventListener('touchmove', function(evt) {
  evt.preventDefault();
});

function closeMessage(element) {
  element.parentElement.style.display = 'none'; // Hide the message
  const messageId = element.parentElement.getAttribute('data-message-id');
  
  // Store the closed message ID in local storage
  const closedMessages = JSON.parse(localStorage.getItem('closed_messages')) || [];
  closedMessages.push(messageId);
  localStorage.setItem('closed_messages', JSON.stringify(closedMessages));
}