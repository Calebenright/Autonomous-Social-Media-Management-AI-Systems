"use strict";

// FIREBASE LISTENER //

import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-app.js';
import { getFirestore, collection, doc, setDoc, getDoc, onSnapshot } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-firestore.js';

var firebaseConfig = {
apiKey: "AIzaSyCJTdpRMOwfhDosa6MTPbsh38kxxiqllc4",
authDomain: "feed-ai-c379d.firebaseapp.com",
projectId: "feed-ai-c379d",
storageBucket: "feed-ai-c379d.appspot.com",
messagingSenderId: "825164430085",
appId: "1:825164430085:web:a41ec57b7c3c0d92c5156c",
measurementId: "G-0K43VDRKJP"
};

// const isLinkedin = userSettings.isLinkedin === true;
// const isFacebook = userSettings.isFacebook === true;
// const isInstagram = userSettings.isInstagram === true;
// const isGoogle = userSettings.isGoogle === true;

const firebaseApp = initializeApp(firebaseConfig);
const db = getFirestore(firebaseApp);
const statusDocRef = doc(collection(db, 'users'), jsonDump.userId);
const linkedinSwitch = document.getElementById('linkedin_switch');
const facebookSwitch = document.getElementById('facebook_switch');
const googleSwitch = document.getElementById('google_business_switch');
const instagramSwitch = document.getElementById('instagram_switch');

function updateStatusInFirestore() {
    onSnapshot(statusDocRef, (docSnapshot) => {
        if (docSnapshot.exists()) {
            let isLinkedin = docSnapshot.data().isLinkedin;
            let isFacebook = docSnapshot.data().isFacebook;
            let isInstagram = docSnapshot.data().isInstagram;
            let isGoogle = docSnapshot.data().isGoogle;

            const userData = {
                isLinkedin: linkedinSwitch.checked,
                isFacebook: facebookSwitch.checked,
                isInstagram: instagramSwitch.checked,
                isGoogle: googleSwitch.checked
            };

            linkedinSwitch.checked = isLinkedin;
            facebookSwitch.checked = isFacebook;
            instagramSwitch.checked = isInstagram;
            googleSwitch.checked = isGoogle;

            setDoc(statusDocRef, userData, { merge: true })
                .then(() => {
                    console.log('Data updated');
                })
                .catch((error) => {
                    console.error('Error updating data to Firestore:', error);
                });
        } else {
            console.error('No Document Exists:', error);
        }
    }, (error) => {
        console.error('Error in realtime listener:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    onSnapshot(statusDocRef, (docSnapshot) => {
        if (docSnapshot.exists()) {
            let isLinkedin = docSnapshot.data().isLinkedin;
            let isFacebook = docSnapshot.data().isFacebook;
            let isInstagram = docSnapshot.data().isInstagram;
            let isGoogle = docSnapshot.data().isGoogle;
            linkedinSwitch.checked = isLinkedin;
            facebookSwitch.checked = isFacebook;
            instagramSwitch.checked = isInstagram;
            googleSwitch.checked = isGoogle;
            console.log(isFacebook);
            console.log(isInstagram);
            console.log(isGoogle);
            console.log(isLinkedin);
        } else {
            console.error('No Document Exists:', error);
        }
    }, (error) => {
        console.error('Error in realtime listener:', error);
    });
});

linkedinSwitch.addEventListener('change', updateStatusInFirestore);
facebookSwitch.addEventListener('change', updateStatusInFirestore);
instagramSwitch.addEventListener('change', updateStatusInFirestore);
googleSwitch.addEventListener('change', updateStatusInFirestore);
