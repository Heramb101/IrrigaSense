import React from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { OptionCard } from '../ui/OptionCard';
import { MOCK_WEATHER_DATA } from '../../services/mockData';

interface WeatherQuestionProps {
  definition: QuestionDefinition;
}

export const WeatherQuestion: React.FC<WeatherQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const weather = state.data.weather;
  const apiWeather = (weather.api_current && Object.keys(weather.api_current).length > 0)
    ? weather.api_current
    : MOCK_WEATHER_DATA;

  const temp = (apiWeather.temperature_c as number) ?? 28.5;
  const humidity = (apiWeather.humidity_percent as number) ?? 62;
  const precip = (apiWeather.precipitation_mm as number) ?? 0;
  const condition = (apiWeather.condition as string) ?? 'Partly Cloudy';
  const icon = (apiWeather.icon as string) ?? '🌤️';

  const isConfirmedYes = weather.user_selection === 'yes';
  const isConfirmedNo = weather.user_selection === 'no';

  const farmerReported = (weather.farmer_reported_weather as Record<string, string>) || {};

  const handleConfirm = (confirmed: boolean) => {
    if (confirmed) {
      updateSectionData('weather', {
        api_current: apiWeather as unknown as Record<string, unknown>,
        farmer_confirmed: true,
        user_selection: 'yes',
        farmer_reported_weather: {},
      });
    } else {
      updateSectionData('weather', {
        api_current: apiWeather as unknown as Record<string, unknown>,
        farmer_confirmed: false,
        user_selection: 'no',
        farmer_reported_weather: {
          temp_feel: farmerReported.temp_feel || 'Warm (28–35°C)',
          rainfall: farmerReported.rainfall || 'Light drizzle',
          air_condition: farmerReported.air_condition || 'Normal',
        },
      });
    }
  };

  const handleCorrectionChange = (key: string, value: string) => {
    updateSectionData('weather', {
      farmer_reported_weather: {
        ...farmerReported,
        [key]: value,
      },
    });
  };

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        {/* Weather Preview Card */}
        <div className="weather-preview-box">
          <div className="weather-primary-row">
            <span className="weather-icon-large">{icon}</span>
            <div className="weather-temp-block">
              <span className="weather-temp-value">{temp}°C</span>
              <span className="weather-condition-text">{condition}</span>
            </div>
          </div>

          <div className="weather-metrics-grid">
            <div className="metric-pill">
              <span className="metric-icon">💧</span>
              <span className="metric-label">Humidity:</span>
              <span className="metric-val">{humidity}%</span>
            </div>
            <div className="metric-pill">
              <span className="metric-icon">🌧️</span>
              <span className="metric-label">Precipitation:</span>
              <span className="metric-val">{precip} mm</span>
            </div>
            <div className="metric-pill">
              <span className="metric-icon">☀️</span>
              <span className="metric-label">Evapotranspiration:</span>
              <span className="metric-val">4.8 mm/day</span>
            </div>
          </div>
        </div>

        {/* Confirmation Buttons */}
        <div className="options-vertical-list">
          <OptionCard
            value="yes"
            label="Yes, matches the weather right now"
            description="Use these environmental values for soil water evaporation calculations"
            icon="✓"
            selected={isConfirmedYes}
            onClick={() => handleConfirm(true)}
          />
          <OptionCard
            value="no"
            label="No, actual weather feels different"
            description="Provide simple manual adjustments for temperature or rain"
            icon="✏️"
            selected={isConfirmedNo}
            onClick={() => handleConfirm(false)}
          />
        </div>

        {/* Manual Weather Correction Controls */}
        {isConfirmedNo && (
          <div className="manual-correction-panel">
            <h4 className="correction-title">How is the weather at your farm right now?</h4>

            <div className="correction-group">
              <label className="correction-label">Temperature Feel:</label>
              <div className="chips-row">
                {['Hot (Above 35°C)', 'Warm (28–35°C)', 'Mild (20–28°C)', 'Cool / Cold (< 20°C)'].map(
                  (opt) => (
                    <button
                      key={opt}
                      type="button"
                      className={`chip-btn ${farmerReported.temp_feel === opt ? 'active' : ''}`}
                      onClick={() => handleCorrectionChange('temp_feel', opt)}
                    >
                      {opt}
                    </button>
                  )
                )}
              </div>
            </div>

            <div className="correction-group">
              <label className="correction-label">Rainfall in last 24–48 hours:</label>
              <div className="chips-row">
                {['No rain (Dry)', 'Light drizzle', 'Moderate rain', 'Heavy downpour'].map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    className={`chip-btn ${farmerReported.rainfall === opt ? 'active' : ''}`}
                    onClick={() => handleCorrectionChange('rainfall', opt)}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
