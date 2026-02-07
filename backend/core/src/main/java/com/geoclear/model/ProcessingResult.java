package com.geoclear.model;

import java.util.List;

/**
 * Result of displacement processing
 */
public class ProcessingResult {
    private List<Feature> features;
    private int overlapsDetected;
    private int overlapsResolved;
    private double maxDisplacementMeters;
    private double processingTimeSeconds;

    public ProcessingResult(List<Feature> features, int overlapsDetected,
            int overlapsResolved, double maxDisplacementMeters,
            double processingTimeSeconds) {
        this.features = features;
        this.overlapsDetected = overlapsDetected;
        this.overlapsResolved = overlapsResolved;
        this.maxDisplacementMeters = maxDisplacementMeters;
        this.processingTimeSeconds = processingTimeSeconds;
    }

    // Getters
    public List<Feature> getFeatures() {
        return features;
    }

    public int getOverlapsDetected() {
        return overlapsDetected;
    }

    public int getOverlapsResolved() {
        return overlapsResolved;
    }

    public int getOverlapsFound() {
        return overlapsDetected;
    }

    public double getMaxDisplacementMeters() {
        return maxDisplacementMeters;
    }

    public double getProcessingTimeSeconds() {
        return processingTimeSeconds;
    }

    public double getProcessingTime() {
        return processingTimeSeconds;
    }
}
