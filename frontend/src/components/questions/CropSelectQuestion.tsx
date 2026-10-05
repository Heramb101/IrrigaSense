import React, { useState, useMemo } from 'react';
import type { QuestionDefinition } from '../../assessment/assessmentConfig';
import { useAssessment } from '../../context/useAssessment';
import { MOCK_CROPS_LIST } from '../../services/mockData';

interface CropSelectQuestionProps {
  definition: QuestionDefinition;
}

export const CropSelectQuestion: React.FC<CropSelectQuestionProps> = ({ definition }) => {
  const { state, updateSectionData } = useAssessment();
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const currentCropId = typeof state.data.crop === 'string'
    ? state.data.crop
    : (state.data.crop as any)?.current_crop_id || '';

  const categories = useMemo(() => {
    const set = new Set(MOCK_CROPS_LIST.map((c) => c.category));
    return ['All', ...Array.from(set)];
  }, []);

  const filteredCrops = useMemo(() => {
    return MOCK_CROPS_LIST.filter((crop) => {
      const matchesSearch =
        crop.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        crop.id.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCat = selectedCategory === 'All' || crop.category === selectedCategory;
      return matchesSearch && matchesCat;
    });
  }, [searchTerm, selectedCategory]);

  const handleSelectCrop = (cropId: string) => {
    updateSectionData('crop', cropId);
  };

  return (
    <div className="question-card" data-question-id={definition.id}>
      <div className="question-header">
        <h2>{definition.title}</h2>
        {definition.subtitle && <p className="question-subtitle">{definition.subtitle}</p>}
      </div>

      <div className="question-body">
        {/* Search input */}
        <div className="search-bar-container">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input-field"
            placeholder="Search crop name (e.g. Wheat, Cotton, Sugarcane, Tomato)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => setSearchTerm('')}
            >
              ✕
            </button>
          )}
        </div>

        {/* Category filter tabs */}
        <div className="category-tabs-row">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              className={`category-tab-btn ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Crop Cards Grid */}
        <div className="crops-grid">
          {filteredCrops.map((crop) => {
            const isSelected = currentCropId.toLowerCase() === crop.id.toLowerCase() || currentCropId.toLowerCase() === crop.name.toLowerCase();
            return (
              <div
                key={crop.id}
                className={`crop-select-card ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSelectCrop(crop.name)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleSelectCrop(crop.name);
                  }
                }}
              >
                <div className="crop-card-top">
                  <span className="crop-category-badge">{crop.category}</span>
                  {isSelected && <span className="crop-check-badge">✓ Selected</span>}
                </div>
                <h3 className="crop-card-name">{crop.name}</h3>
                <span className="crop-duration-info">⏱️ ~{crop.typicalDurationDays} days cycle</span>
              </div>
            );
          })}
        </div>

        {filteredCrops.length === 0 && (
          <div className="no-results-box">
            <p>No crops match "{searchTerm}". Try searching in English or general crop name.</p>
          </div>
        )}
      </div>
    </div>
  );
};
