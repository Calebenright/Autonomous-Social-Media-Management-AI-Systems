"use strict";

// FIREBASE LISTENER //

import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-app.js';
import { getAuth, GoogleAuthProvider, FacebookAuthProvider, signInWithPopup, signInWithEmailAndPassword, setPersistence, browserLocalPersistence } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-auth.js';

var firebaseConfig = {
  apiKey: "AIzaSyCJTdpRMOwfhDosa6MTPbsh38kxxiqllc4",
  authDomain: "feed-ai-c379d.firebaseapp.com",
  projectId: "feed-ai-c379d",
  storageBucket: "feed-ai-c379d.appspot.com",
  messagingSenderId: "825164430085",
  appId: "1:825164430085:web:a41ec57b7c3c0d92c5156c",
  measurementId: "G-0K43VDRKJP"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

function displayErrorMessage(errorMsg) {
  var errorMessagesContainer = document.getElementById('error-messages-container');

  if (errorMessagesContainer.querySelectorAll('.messages').length === 0) {
      var messagesUl = document.createElement('ul');
      messagesUl.className = 'messages';
      errorMessagesContainer.appendChild(messagesUl);
  }

  var errorMessageLi = document.createElement('li');
  errorMessageLi.className = 'danger';
  errorMessageLi.setAttribute('data-message-id', 'ajaxError');
  errorMessageLi.textContent = errorMsg;
  var closeButton = document.createElement('span');
  closeButton.className = 'closebtn';
  closeButton.innerHTML = '&times;';
  closeButton.onclick = function() { closeMessage(this); };
  errorMessageLi.appendChild(closeButton);
  errorMessagesContainer.querySelector('.messages').appendChild(errorMessageLi);
}

function signInWithFeadlio() {
  document.getElementById('loader').style.display = 'flex';
  document.getElementById('feadlio-sign-in').disabled = true;

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  signInWithEmailAndPassword(auth, email, password)
      .then((userCredential) => {
        console.log('@$ signin with feadlio worked!' + userCredential);
        updateIsProviderStatus();
        document.getElementById('email').value = email;
        document.getElementById('password').value = password;
        document.getElementById('providerField').value = "feadlio.com";
        document.getElementById('loginForm').submit();
      })
      .catch((error) => {
          console.error("Login Failed: ", error.message);
          displayErrorMessage("Invalid Login")
          document.getElementById('loader').style.display = 'none';
          document.getElementById('feadlio-sign-in').disabled = false;
    });
}

document.getElementById('feadlio-sign-in').addEventListener('click', signInWithFeadlio);

document.getElementById('google-sign-in').addEventListener('click', function() {
  document.getElementById('loader').style.display = 'flex';
  document.getElementById('google-sign-in').disabled = true;
  window.location.href = '/google_signin/';
});

document.addEventListener("DOMContentLoaded", function() {
  console.log('got provider: ', isProvider);
  if (isProvider == 'True') {
    console.log('do not run: ', isProvider);
    if (userEmail && userPid) {
      console.log('userEmail: ', userEmail);
      console.log('userPid: ', userPid);
      signInWithEmailAndPassword(auth, userEmail, userPid)
        .then((userCredential) => {
            updateIsProviderStatus().then(() => {
                window.location.href = "/dashboard/";
            }).catch((error) => {
                console.error("Failed to update provider status: ", error.message);
                displayErrorMessage("Failed to login. If the problem persists please contact us.");
            });
        })
        .catch((error) => {
          console.error("Login Failed: ", error.message);
          displayErrorMessage("Invalid Login");
        });
    } else {
      console.log("No credentials provided, skipping automatic sign-in.");
    }
  }
})

function getCookie(name) {
  const cookieValue = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return cookieValue ? cookieValue.pop() : '';
}

function updateIsProviderStatus() {
  var csrfToken = getCookie('csrftoken');
  fetch('/update_is_provider/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken, 
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({isProvider: false})
  })
  .then(response => {
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
  })
  .then(data => {
    console.log('Fetch successful:', data);
  })
  .catch(error => {
    console.error('Error during fetch operation:', error);
  });
}
