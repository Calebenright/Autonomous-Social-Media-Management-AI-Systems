"use strict";

// FIREBASE LISTENER //

import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-app.js';
import { getFirestore, collection, doc, setDoc, getDoc, onSnapshot } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-firestore.js';
import { getAuth, GoogleAuthProvider, signInWithRedirect, FacebookAuthProvider, signInWithEmailAndPassword, setPersistence, browserLocalPersistence, getRedirectResult } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-auth.js';

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

setPersistence(auth, browserLocalPersistence)
  .then(() => {})
  .catch((error) => {
    console.error("Error setting persistence: ", error.message);
  });

  function signInWithFeadlio() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            document.getElementById('providerField').value = "feadlio.com";
            document.getElementById('loginForm').submit();
        })
        .catch((error) => {
            console.error("Login Failed: ", error.message);
            displayErrorMessage("Invalid Login")
      });
  }

function signInWithGoogle() {
  const googleProvider = new GoogleAuthProvider();
  signInWithRedirect(auth, googleProvider);
}

function signInWithFacebook() {
  const facebookProvider = new FacebookAuthProvider();
  signInWithRedirect(auth, facebookProvider);
}

getRedirectResult(auth)
  .then((result) => {
      if (result) {
        if (result.operationType == 'signIn') {
          const user = result.user;
          user.getIdToken().then((idToken) => {
            document.getElementById('providerField').value = result.providerId;
            document.getElementById('uidField').value = user.uid;
            document.getElementById('tokenField').value = idToken;

            document.getElementById('loginForm').submit();
          });
        }
      }
  }).catch((error) => {
      console.error("Error during sign-in:", error);
  });

document.getElementById('feadlio-sign-in').addEventListener('click', signInWithFeadlio);
document.getElementById('google-sign-in').addEventListener('click', signInWithGoogle);
// document.getElementById('facebook-sign-in').addEventListener('click', signInWithFacebook);

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
