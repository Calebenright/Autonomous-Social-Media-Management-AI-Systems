"use strict";

// FIREBASE LISTENER //

import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-app.js';
import { getFirestore, collection, doc, setDoc, getDoc, onSnapshot } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-firestore.js';
import { getAuth, GoogleAuthProvider, signInWithPopup, FacebookAuthProvider, signInWithEmailAndPassword, setPersistence} from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-auth.js';

var firebaseConfig = {
  apiKey: "AIzaSyCJTdpRMOwfhDosa6MTPbsh38kxxiqllc4",
  authDomain: "feed-ai-c379d.firebaseapp.com",
  projectId: "feed-ai-c379d",
  storageBucket: "feed-ai-c379d.appspot.com",
  messagingSenderId: "825164430085",
  appId: "1:825164430085:web:a41ec57b7c3c0d92c5156c",
  measurementId: "G-0K43VDRKJP"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

setPersistence(authInstance, firebase.auth.Auth.Persistence.LOCAL)
  .catch((error) => {
    console.error("Error setting persistence: ", error.message);
  });

document.addEventListener('DOMContentLoaded', function () {
  const loginForm = document.querySelector('form');
  loginForm.addEventListener('submit', function (e) {
      e.preventDefault();

      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;

      signInWithEmailAndPassword(auth, email, password)
          .then((userCredential) => {
              console.error("Successful Login");
              loginForm.submit();
          })
          .catch((error) => {
              console.error("Error with Firebase Auth: ", error.message);
          });
  });
});

// Google Sign-In
function signInWithGoogle() {
  const googleProvider = new GoogleAuthProvider();

  signInWithPopup(auth, googleProvider).then((result) => {
    console.log("Google sign-in successful!");
    console.log("User details:", result.user);
  }).catch((error) => {
    console.error("Google sign-in failed:", error.message);
  });
}

// Facebook Sign-In
function signInWithFacebook() {
  const facebookProvider = new FacebookAuthProvider();

  signInWithPopup(auth, facebookProvider).then((result) => {
    console.log("Facebook sign-in successful!");
    console.log("User details:", result.user);
  }).catch((error) => {
    console.error("Facebook sign-in failed:", error.message);
  });
}

// You can call these functions with a button click
document.getElementById('google-sign-in').addEventListener('click', signInWithGoogle);
document.getElementById('facebook-sign-in').addEventListener('click', signInWithFacebook);
