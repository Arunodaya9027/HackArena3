package com.geoclear.model;

/**
 * Priority levels for feature classification
 * Used for displacement algorithm ordering
 */
public enum FeaturePriority {
    P1_MOTORWAY(1),
    P2_PRIMARY(2),
    P3_STREET(3),
    P4_BUILDING(4),
    P5_LABEL(5);

    private final int value;

    FeaturePriority(int value) {
        this.value = value;
    }

    public int getValue() {
        return value;
    }

    public static FeaturePriority fromValue(int value) {
        for (FeaturePriority priority : values()) {
            if (priority.value == value) {
                return priority;
            }
        }
        return P3_STREET; // Default
    }
}
