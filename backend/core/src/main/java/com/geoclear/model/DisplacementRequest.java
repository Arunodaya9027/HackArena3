package com.geoclear.model;

import java.util.List;

/**
 * Request DTO for displacement processing
 */
public class DisplacementRequest {
    private List<Feature> features;

    public List<Feature> getFeatures() {
        return features;
    }

    public void setFeatures(List<Feature> features) {
        this.features = features;
    }
}