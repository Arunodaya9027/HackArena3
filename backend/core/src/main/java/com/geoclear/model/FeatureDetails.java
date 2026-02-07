package com.geoclear.model;

import java.util.List;

/**
 * Detailed feature information for popup display
 */
public class FeatureDetails {
    private String id;
    private String type;
    private String priority;
    private int width;
    private String color;
    private int zIndex;
    private boolean displaced;
    private Double displacementDistance;
    private Double displacementAngle;
    private List<Coordinate> coords;
    private List<Coordinate> originalCoords;

    public FeatureDetails(Feature feature) {
        this.id = feature.getId();
        this.type = feature.getType();
        this.priority = feature.getPriority().name();
        this.width = (int) feature.getWidth();
        this.color = feature.getColor();
        this.zIndex = feature.getZIndex();
        this.displaced = feature.isDisplaced();
        this.coords = feature.getCoords();
        this.originalCoords = feature.getOriginalCoords();

        // Calculate displacement metrics
        if (displaced && originalCoords != null && coords != null && !coords.isEmpty() && !originalCoords.isEmpty()) {
            Coordinate orig = originalCoords.get(0);
            Coordinate curr = coords.get(0);
            this.displacementDistance = calculateDistance(orig, curr);
            this.displacementAngle = calculateAngle(orig, curr);
        }
    }

    private double calculateDistance(Coordinate c1, Coordinate c2) {
        final double R = 6371000; // Earth radius in meters
        double lat1 = Math.toRadians(c1.getLat());
        double lat2 = Math.toRadians(c2.getLat());
        double dLat = Math.toRadians(c2.getLat() - c1.getLat());
        double dLng = Math.toRadians(c2.getLng() - c1.getLng());

        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(lat1) * Math.cos(lat2) *
                        Math.sin(dLng / 2) * Math.sin(dLng / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

        return R * c;
    }

    private double calculateAngle(Coordinate c1, Coordinate c2) {
        double dLng = c2.getLng() - c1.getLng();
        double dLat = c2.getLat() - c1.getLat();
        double angle = Math.toDegrees(Math.atan2(dLng, dLat));
        return (angle + 360) % 360; // Normalize to 0-360
    }

    // Getters and setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getPriority() {
        return priority;
    }

    public void setPriority(String priority) {
        this.priority = priority;
    }

    public int getWidth() {
        return width;
    }

    public void setWidth(int width) {
        this.width = width;
    }

    public String getColor() {
        return color;
    }

    public void setColor(String color) {
        this.color = color;
    }

    public int getZIndex() {
        return zIndex;
    }

    public void setZIndex(int zIndex) {
        this.zIndex = zIndex;
    }

    public boolean isDisplaced() {
        return displaced;
    }

    public void setDisplaced(boolean displaced) {
        this.displaced = displaced;
    }

    public Double getDisplacementDistance() {
        return displacementDistance;
    }

    public void setDisplacementDistance(Double displacementDistance) {
        this.displacementDistance = displacementDistance;
    }

    public Double getDisplacementAngle() {
        return displacementAngle;
    }

    public void setDisplacementAngle(Double displacementAngle) {
        this.displacementAngle = displacementAngle;
    }

    public List<Coordinate> getCoords() {
        return coords;
    }

    public void setCoords(List<Coordinate> coords) {
        this.coords = coords;
    }

    public List<Coordinate> getOriginalCoords() {
        return originalCoords;
    }

    public void setOriginalCoords(List<Coordinate> originalCoords) {
        this.originalCoords = originalCoords;
    }
}
