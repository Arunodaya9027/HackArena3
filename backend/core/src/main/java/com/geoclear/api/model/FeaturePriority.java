package com.geoclear.api.model;

/**
 * Enhanced Feature Priority System - Multi-category Classification
 * 
 * Priority Hierarchy (Higher = More Important):
 * P1: Critical Infrastructure (Highways, Railways, Rivers)
 * P2: Major Roads (Main Roads)
 * P3: Local Streets (Local Roads)
 * P4: Structures (Buildings, Parks)
 * P5: Decorative (Icons, Labels, Overlap Areas)
 * 
 * Display widths optimized for visual hierarchy
 */
public enum FeaturePriority {
    // P1: Critical Infrastructure (5.0pt - Widest, Highest Priority)
    P1_HIGHWAY("P1_HIGHWAY", 5.0, 1, "Highway/Expressway"),
    P1_RAILWAY("P1_RAILWAY", 4.5, 1, "Railway Line"),
    P1_RIVER("P1_RIVER", 4.0, 1, "River/Water Body"),

    // P2: Major Roads (3.5pt - Major Arteries)
    P2_MAIN_ROAD("P2_MAIN_ROAD", 3.5, 2, "Main Road/Avenue"),

    // P3: Local Roads (3.0pt - Standard Streets)
    P3_LOCAL_ROAD("P3_LOCAL_ROAD", 3.0, 3, "Local Road/Street"),
    P3_STREET("P3_STREET", 2.8, 3, "Street/Lane"),

    // P4: Structures (2.5pt - Buildings & Parks)
    P4_BUILDING("P4_BUILDING", 2.5, 4, "Building/Structure"),
    P4_PARK("P4_PARK", 2.5, 4, "Park/Green Space"),

    // P5: Decorative Elements (2.0pt - Labels, Icons)
    P5_LABEL("P5_LABEL", 2.0, 5, "Text Label"),
    P5_ICON("P5_ICON", 2.0, 5, "Map Icon"),
    P5_OVERLAP_AREA("P5_OVERLAP_AREA", 1.5, 5, "Overlap Area"),

    // Backward compatibility (deprecated - use specific types)
    @Deprecated
    P2_ROAD("P2_ROAD", 3.0, 3, "Road (Legacy)");

    private final String code;
    private final double displayWidth;
    private final int priorityLevel;
    private final String description;

    FeaturePriority(String code, double displayWidth, int priorityLevel, String description) {
        this.code = code;
        this.displayWidth = displayWidth;
        this.priorityLevel = priorityLevel;
        this.description = description;
    }

    public String getCode() {
        return code;
    }

    public double getDisplayWidth() {
        return displayWidth;
    }

    public int getPriorityLevel() {
        return priorityLevel;
    }

    public String getDescription() {
        return description;
    }

    @Override
    public String toString() {
        return code;
    }
}
