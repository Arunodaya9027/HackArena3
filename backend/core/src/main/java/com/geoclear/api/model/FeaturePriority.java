package com.geoclear.api.model;

/**
 * Feature priority levels
 * P1_HIGHWAY: Width 5pt (higher priority)
 * P2_ROAD: Width 3pt (lower priority)
 */
public enum FeaturePriority {
    P1_HIGHWAY("P1_HIGHWAY", 5.0),
    P2_ROAD("P2_ROAD", 3.0);

    private final String code;
    private final double displayWidth;

    FeaturePriority(String code, double displayWidth) {
        this.code = code;
        this.displayWidth = displayWidth;
    }

    public String getCode() {
        return code;
    }

    public double getDisplayWidth() {
        return displayWidth;
    }

    @Override
    public String toString() {
        return code;
    }
}
