package com.geoclear.api.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Result of displacement processing for a single feature
 */
public class DisplacementResult {

    @JsonProperty("feature_id")
    private String featureId;

    @JsonProperty("original_wkt")
    private String originalWkt;

    @JsonProperty("corrected_wkt")
    private String correctedWkt;

    @JsonProperty("was_displaced")
    private boolean wasDisplaced;

    private ConflictMetadata metadata;

    public DisplacementResult() {
    }

    public DisplacementResult(String featureId, String originalWkt, String correctedWkt,
            boolean wasDisplaced, ConflictMetadata metadata) {
        this.featureId = featureId;
        this.originalWkt = originalWkt;
        this.correctedWkt = correctedWkt;
        this.wasDisplaced = wasDisplaced;
        this.metadata = metadata;
    }

    // Getters and Setters
    public String getFeatureId() {
        return featureId;
    }

    public void setFeatureId(String featureId) {
        this.featureId = featureId;
    }

    public String getOriginalWkt() {
        return originalWkt;
    }

    public void setOriginalWkt(String originalWkt) {
        this.originalWkt = originalWkt;
    }

    public String getCorrectedWkt() {
        return correctedWkt;
    }

    public void setCorrectedWkt(String correctedWkt) {
        this.correctedWkt = correctedWkt;
    }

    public boolean isWasDisplaced() {
        return wasDisplaced;
    }

    public void setWasDisplaced(boolean wasDisplaced) {
        this.wasDisplaced = wasDisplaced;
    }

    public ConflictMetadata getMetadata() {
        return metadata;
    }

    public void setMetadata(ConflictMetadata metadata) {
        this.metadata = metadata;
    }

    @Override
    public String toString() {
        return "DisplacementResult{" +
                "featureId='" + featureId + '\'' +
                ", wasDisplaced=" + wasDisplaced +
                ", metadata=" + metadata +
                '}';
    }
}
