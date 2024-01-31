"use strict";

import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-app.js';
import { getFirestore, collection, getDocs } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-firestore.js';
import { getAuth, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/9.6.6/firebase-auth.js';

var firebaseConfig = {
    apiKey: "AIzaSyCJTdpRMOwfhDosa6MTPbsh38kxxiqllc4",
    authDomain: "feed-ai-c379d.firebaseapp.com",
    projectId: "feed-ai-c379d",
    storageBucket: "feed-ai-c379d.appspot.com",
    messagingSenderId: "825164430085",
    appId: "1:825164430085:web:a41ec57b7c3c0d92c5156c",
    measurementId: "G-0K43VDRKJP"
    };

const firebaseApp = initializeApp(firebaseConfig);
const auth = getAuth(firebaseApp);
const db = getFirestore(firebaseApp);

onAuthStateChanged(auth, (user) => {
    if (user) {
        console.log('User is signed in.');
    } else {
        window.location.href = '/login/';
    }
});

function loadAccounts() {
    const selectElement = document.getElementById('accountSelect');
    
    getDocs(collection(db, 'accounts')).then(querySnapshot => {
        querySnapshot.forEach(doc => {
            const accountName = doc.data().name;
            const accountId = doc.id;

            const option = document.createElement('option');
            option.textContent = accountName;
            option.value = accountId;
            selectElement.appendChild(option);
        });
    }).catch(error => {
        console.error('Error fetching accounts:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    loadAccounts(); 
});