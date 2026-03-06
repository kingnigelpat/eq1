// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-analytics.js";
import { getAuth, sendPasswordResetEmail, signInWithEmailAndPassword, createUserWithEmailAndPassword, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/11.3.1/firebase-auth.js";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyDAwlHxu8ylW90Vx2P1XSQNWT6l7IPZNto",
    authDomain: "eq-rae.firebaseapp.com",
    projectId: "eq-rae",
    storageBucket: "eq-rae.firebasestorage.app",
    messagingSenderId: "932271396527",
    appId: "1:932271396527:web:60d84c874d7099135f665a",
    measurementId: "G-V3VZ0PWW4D"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth = getAuth(app);

export { auth, sendPasswordResetEmail, signInWithEmailAndPassword, createUserWithEmailAndPassword, onAuthStateChanged };
