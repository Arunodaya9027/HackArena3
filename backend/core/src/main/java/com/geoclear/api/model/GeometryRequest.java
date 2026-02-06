package com.geoclear.api.model;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Positive;
import java.util.List;

/**
 * Request for geometry processing
 */
public class GeometryRequest {

    @NotEmpty(message = "Features list cannot be empty")
    @Valid
    private List<FeatureInput> features;

    @Positive(message = "Min clearance must be positive")
    private double minClearance = 2.0;

    public GeometryRequest() {
    }

    public GeometryRequest(List<FeatureInput> features, double minClearance) {
        this.features = features;
        this.minClearance = minClearance;
    }

    public List<FeatureInput> getFeatures() {
        return features;
    }

    public void setFeatures(List<FeatureInput> features) {
        this.features = features;
    }

    public double getMinClearance() {
        return minClearance;
    }

    public void setMinClearance(double minClearance) {
        this.minClearance = minClearance;
    }

    @Override
    public String toString() {
        return "GeometryRequest{" +
                "featuresCount=" + (features != null ? features.size() : 0) +
                ", minClearance=" + minClearance +
                '}';
    }
}
