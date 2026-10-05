/* eslint-disable @typescript-eslint/no-explicit-any */
// Ambient type definitions for Google Maps JavaScript API
declare global {
  namespace google {
    namespace maps {
      interface ImportLibraryMap {
        maps: any;
        places: any;
        geometry: any;
        marker: any;
        geocoding: any;
      }

      type MapTypeId = string;
      const MapTypeId: {
        ROADMAP: string;
        SATELLITE: string;
        HYBRID: string;
        TERRAIN: string;
      };

      const Animation: {
        DROP: number;
        BOUNCE: number;
      };

      interface LatLngLiteral {
        lat: number;
        lng: number;
      }

      interface LatLng {
        lat(): number;
        lng(): number;
      }

      interface MapMouseEvent {
        latLng?: LatLng | null;
      }

      interface MapOptions {
        center?: LatLngLiteral | LatLng;
        zoom?: number;
        mapTypeId?: string;
        mapTypeControl?: boolean;
        mapTypeControlOptions?: any;
        streetViewControl?: boolean;
        fullscreenControl?: boolean;
        zoomControl?: boolean;
        gestureHandling?: string;
        tilt?: number;
      }

      class Map {
        constructor(mapDiv: HTMLElement, opts?: MapOptions);
        setCenter(latLng: LatLngLiteral | LatLng): void;
        setZoom(zoom: number): void;
        getCenter(): LatLng | undefined;
        getZoom(): number | undefined;
        panTo(latLng: LatLngLiteral | LatLng): void;
        setMapTypeId(type: string): void;
        addListener(eventName: string, handler: (e?: any) => void): any;
      }

      interface MarkerOptions {
        position: LatLngLiteral | LatLng;
        map?: Map;
        title?: string;
        draggable?: boolean;
        animation?: any;
      }

      class Marker {
        constructor(opts?: MarkerOptions);
        setPosition(latLng: LatLngLiteral | LatLng): void;
        getPosition(): LatLng | undefined;
        setMap(map: Map | null): void;
        addListener(eventName: string, handler: (e?: any) => void): any;
      }

      interface GeocoderRequest {
        location?: LatLngLiteral | LatLng;
      }

      interface GeocoderResult {
        formatted_address: string;
        address_components?: any[];
      }

      class Geocoder {
        geocode(
          request: GeocoderRequest,
          callback: (results: GeocoderResult[] | null, status: string) => void
        ): void;
      }

      const GeocoderStatus: {
        OK: string;
        ZERO_RESULTS: string;
      };

      namespace places {
        interface PlaceResult {
          formatted_address?: string;
          name?: string;
          geometry?: {
            location?: LatLng;
          };
        }

        interface AutocompleteOptions {
          fields?: string[];
          types?: string[];
        }

        class Autocomplete {
          constructor(inputField: HTMLInputElement, opts?: AutocompleteOptions);
          addListener(eventName: string, handler: () => void): any;
          getPlace(): PlaceResult;
        }
      }
    }
  }

  interface Window {
    google?: typeof google;
  }
}

export {};
