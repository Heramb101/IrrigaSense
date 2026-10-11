import React, { useEffect, useState, useCallback } from 'react';
import { useAssessment } from '../context/useAssessment';
import { decisionApi } from '../services/api';
import type { DashboardRecommendation, FarmLocationInfo } from './dashboardTypes';
import { DashboardLoading } from '../components/dashboard/DashboardLoading';
import { RecommendationCard } from '../components/dashboard/RecommendationCard';
import { SoilMoistureCard } from '../components/dashboard/SoilMoistureCard';
import { SatelliteMapCard } from '../components/dashboard/SatelliteMapCard';
import { CropFarmCard } from '../components/dashboard/CropFarmCard';
import { WeatherCard } from '../components/dashboard/WeatherCard';
import { WaterAvailabilityCard } from '../components/dashboard/WaterAvailabilityCard';

interface DashboardProps {
  onStartNewAssessment?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onStartNewAssessment }) => {
  const { finalSubmission, state, resetAssessment } = useAssessment();

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<DashboardRecommendation | null>(null);

  // Extract assessment data from final submission or live state
  const assessmentData = finalSubmission?.payload.data || state.data;
  const loc = assessmentData?.location;

  const farmLocation: FarmLocationInfo = {
    latitude: loc?.latitude || 18.155,
    longitude: loc?.longitude || 74.580,
    place_name:
      loc?.place_name ||
      assessmentData?.place_name ||
      'Baramati Farmland, Pune District, Maharashtra',
  };

  const cropName =
    typeof assessmentData?.crop === 'string'
      ? assessmentData.crop
      : (assessmentData?.crop as any)?.current_crop_id || 'Tomato';

  const plantingDate = assessmentData?.planting_date || '2026-08-15';
  const farmSize = assessmentData?.farm_size || '2–5 acres';
  const irrigationMethod = assessmentData?.irrigation_method || 'Drip';
  const waterAvailability = assessmentData?.water_availability || 'Moderate';

  const fetchRecommendation = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setRecommendation(null); // Invalidate any previous/stale recommendation on fresh fetch

    try {
      const response = await decisionApi.getRecommendation({
        crop_name: cropName,
        planting_date: plantingDate,
        latitude: farmLocation.latitude,
        longitude: farmLocation.longitude,
        farm_size: farmSize,
        irrigation_method: irrigationMethod,
        water_availability: waterAvailability,
      });

      if (!response || !response.decision || !response.confidence) {
        throw new Error('Received malformed or incomplete recommendation data from server.');
      }

      setRecommendation(response);
      setError(null);
    } catch (err: any) {
      console.warn('Backend decision API request failed:', err?.message);
      // Strictly clear recommendation: never fabricate a successful advisory on error
      setRecommendation(null);
      setError(
        err?.message ||
          'Unable to connect to the recommendation service. An accurate advisory cannot be determined right now. Please check your network connection or server status and retry.'
      );
    } finally {
      setIsLoading(false);
    }
  }, [
    cropName,
    plantingDate,
    farmLocation.latitude,
    farmLocation.longitude,
    farmSize,
    irrigationMethod,
    waterAvailability,
  ]);

  useEffect(() => {
    fetchRecommendation();
  }, [fetchRecommendation]);

  const handleStartNew = () => {
    if (onStartNewAssessment) {
      onStartNewAssessment();
    } else {
      resetAssessment();
    }
  };

  const formattedTimestamp = recommendation?.last_updated
    ? new Date(recommendation.last_updated).toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : new Date().toLocaleDateString();

  return (
    <div className="farmer-dashboard-view" data-testid="farmer-dashboard">
      {/* 1. Dashboard Header */}
      <header className="dashboard-top-header">
        <div className="dashboard-header-brand">
          <div className="brand-title-badge-row">
            <h1 className="dashboard-brand-title">🌱 IrrigaSense</h1>
            <span className="dashboard-live-badge">Live Advisory</span>
          </div>
          <p className="dashboard-farm-location-label">
            📍 {farmLocation.place_name}
          </p>
        </div>

        <div className="dashboard-header-actions">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={fetchRecommendation}
            disabled={isLoading}
            title="Re-run recommendation analysis"
            data-testid="dashboard-refresh-btn"
          >
            ↻ Refresh
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={handleStartNew}
            title="Start a new farm checkup"
          >
            ↺ New Assessment
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      {isLoading ? (
        <DashboardLoading />
      ) : error ? (
        <div className="dashboard-error-state" role="alert" data-testid="dashboard-error-state">
          <div className="error-state-card">
            <span className="error-state-icon">⚠️</span>
            <h2 className="error-state-heading">Recommendation Temporarily Unavailable</h2>
            <p className="error-state-desc">{error}</p>
            <div className="error-state-advisory-box">
              <p className="error-state-advisory">
                <strong>Agronomic Advisory:</strong> IrrigaSense cannot safely provide an irrigation decision without live environmental telemetry and model inference. Do not assume irrigation is unnecessary.
              </p>
            </div>
            <div className="error-state-actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={fetchRecommendation}
                data-testid="retry-recommendation-btn"
              >
                ↻ Retry Analysis
              </button>
              <button
                type="button"
                className="btn btn-outline"
                onClick={handleStartNew}
              >
                ↺ New Assessment
              </button>
            </div>
          </div>
        </div>
      ) : recommendation ? (
        <main className="dashboard-cards-container">
          {/* 2. Main Irrigation Recommendation Card (Visually dominant) */}
          <RecommendationCard recommendation={recommendation} />

          {/* 3. Soil Moisture Card */}
          <SoilMoistureCard recommendation={recommendation} />

          {/* 4. Satellite / Map Card */}
          <SatelliteMapCard location={farmLocation} />

          {/* 5. Crop & Farm Card */}
          <CropFarmCard
            recommendation={recommendation}
            plantingDate={plantingDate}
            farmSize={farmSize}
          />

          {/* 6. Weather Card */}
          <WeatherCard weather={recommendation.weather_summary} />

          {/* 7. Water Availability Card */}
          <WaterAvailabilityCard recommendation={recommendation} />

          {/* 8. Audit & Last Updated Footer */}
          <footer className="dashboard-footer-meta">
            <div className="footer-timestamp-row">
              <span>Recommendation evaluated: <strong>{formattedTimestamp}</strong></span>
              <span className="footer-sep">&bull;</span>
              <span>Farm Plot: {farmLocation.latitude.toFixed(4)}° N, {farmLocation.longitude.toFixed(4)}° E</span>
            </div>
            <p className="footer-disclaimer">
              IrrigaSense Adaptive Decision Engine &bull; FAO-56 depletion and root-zone water balance model.
              Provides timing and need advisory. Consult on-field agronomists for volumetric prescriptions.
            </p>
          </footer>
        </main>
      ) : (
        <div className="dashboard-empty-card">
          <h2>No Recommendation Available</h2>
          <p>Please complete a farm checkup to generate an irrigation recommendation.</p>
          <button type="button" className="btn btn-primary" onClick={handleStartNew}>
            Start Assessment
          </button>
        </div>
      )}
    </div>
  );
};
