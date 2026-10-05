/**
 * Google Maps JavaScript API Dynamic Loader
 * Uses Google's official @googlemaps/js-api-loader functional API.
 */
import { setOptions, importLibrary } from '@googlemaps/js-api-loader';

let isConfigured = false;
let loadPromise: Promise<void> | null = null;

export function isGoogleMapsLoaded(): boolean {
  return typeof window !== 'undefined' && Boolean(window.google?.maps?.Map);
}

export function loadGoogleMapsScript(apiKey: string): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Window is undefined'));
  }

  // If already loaded and Map class available, resolve immediately
  if (isGoogleMapsLoaded()) {
    return Promise.resolve();
  }

  if (loadPromise) {
    return loadPromise;
  }

  try {
    if (!isConfigured) {
      setOptions({
        key: apiKey,
        v: 'weekly',
      });
      isConfigured = true;
    }

    loadPromise = Promise.all([
      importLibrary('maps'),
      importLibrary('places'),
    ])
      .then(() => {
        // Libraries loaded successfully into window.google.maps
      })
      .catch((err: any) => {
        loadPromise = null;
        throw new Error(
          err?.message ||
            'Failed to load Google Maps JavaScript API. Please check your network connection and ensure your API key is authorized.'
        );
      });

    return loadPromise;
  } catch (err: any) {
    loadPromise = null;
    return Promise.reject(
      new Error(
        err?.message || 'Failed to initialize Google Maps JavaScript API.'
      )
    );
  }
}
