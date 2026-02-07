package com.geoclear.model;

import java.util.List;
import java.util.Map;

/**
 * Result of WKT processing operation
 */
public class WktProcessingResult {
    private List<Feature> features;
    private Map<String, Object> metrics;

    public WktProcessingResult(List<Feature> features, Map<String, Object> metrics) {
        this.features = features;
        this.metrics = metrics;
    }

    public List<Feature> getFeatures() {
        return features;
    }

    public void setFeatures(List<Feature> features) {
        this.features = features;
    }

    public Map<String, Object> getMetrics() {
        return metrics;
    }

    public void setMetrics(Map<String, Object> metrics) {
        this.metrics = metrics;
    }
}
