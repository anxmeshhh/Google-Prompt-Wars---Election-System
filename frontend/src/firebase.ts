/**
 * ElectaVerse — Firebase Client SDK Configuration
 * Initializes Firebase App and Google Analytics for production telemetry.
 */

import { initializeApp } from 'firebase/app';
import { getAnalytics, logEvent, isSupported } from 'firebase/analytics';

const firebaseConfig = {
  apiKey: 'AIzaSyBHuACpAlqimxJ6IgojlfPOJwVuff_lFOI',
  authDomain: 'electaverse.firebaseapp.com',
  projectId: 'electaverse',
  storageBucket: 'electaverse.firebasestorage.app',
  messagingSenderId: '672280729573',
  appId: '1:672280729573:web:c48d382f7a910df23b810c',
  measurementId: 'G-FNGXSVEW8K',
};

// Initialize Firebase App
const app = initializeApp(firebaseConfig);

// Initialize Analytics (only in production browser environments)
let analytics: ReturnType<typeof getAnalytics> | null = null;

isSupported().then((supported) => {
  if (supported) {
    analytics = getAnalytics(app);
    console.log('📊 Firebase Analytics initialized');
  }
});

/**
 * Log a custom event to Firebase Analytics.
 * Safe to call even if analytics is not available.
 */
export const trackEvent = (eventName: string, params?: Record<string, unknown>) => {
  if (analytics) {
    logEvent(analytics, eventName, params);
  }
};

export { app, analytics };
