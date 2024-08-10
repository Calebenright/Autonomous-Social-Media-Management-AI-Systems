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
  const email = document.getElementById('email').value;
  getPassword(email);
}

document.getElementById('feadlio-sign-in').addEventListener('click', signInWithFeadlio);

function getCookie(name) {
  const cookieValue = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return cookieValue ? cookieValue.pop() : '';
}

function getPassword(email) {
  var csrfToken = getCookie('csrftoken');
  fetch('/get_password/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken, 
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({email: email})
  })
  .then(response => {
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
  })
  .then(data => {
    if (data.password) {
      const password = data.password;
      const pid = data.pid;
      console.log(email, password)
      signInWithEmailAndPassword(auth, email, password)
      .then((userCredential) => {
        console.log('@$ signin with feadlio worked!' + userCredential);
        document.getElementById('loginForm').submit();
      })
      .catch((error) => {
        signInWithEmailAndPassword(auth, email, pid)
        .then((userCredential) => {
          console.log('@$ signin with feadlio worked!' + userCredential);
          document.getElementById('loginForm').submit();
        })
        .catch((error) => {
            console.error("Login Failed: ", error.message);
            if (error.code === 'auth/wrong-password') {
                displayErrorMessage("Username or password is incorrect");
            } else {
                displayErrorMessage("Invalid login");
            }
            document.getElementById('loader').style.display = 'none';
        });
      });
    } else {
      throw new Error('Password not found in response');
    }
  })
  .catch(error => {
    displayErrorMessage("An error occured while logging in. Please try again. or contact us.");
  });
}