package com.geoclear.model;

import java.util.List;

/**
 * Represents a geographic feature (road, river, etc.)
 */
public class Feature {
    private String id;
    private String type;
    private FeaturePriority priority;
    private double width;
    private String color;
    private int zIndex;
    private List<Coordinate> coords;
    private List<Coordinate> originalCoords;
    private boolean displaced;

    public Feature() {
    }

    public Feature(String id, String type, FeaturePriority priority, double width, String color,
            int zIndex, List<Coordinate> coords, List<Coordinate> originalCoords, boolean displaced) {
        this.id = id;
        this.type = type;
        this.priority = priority;
        this.width = width;
        this.color = color;
        this.zIndex = zIndex;
        this.coords = coords;
        this.originalCoords = originalCoords;
        this.displaced = displaced;
    }

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

    public FeaturePriority getPriority() {
        return priority;
    }

    public void setPriority(FeaturePriority priority) {
        this.priority = priority;
    }

    public double getWidth() {
        return width;
    }

    public void setWidth(double width) {
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

    public boolean isDisplaced() {
        return displaced;
    }

    public void setDisplaced(boolean displaced) {
        this.displaced = displaced;
    }

    /**
     * Calculate bounding box for this feature
     */
    public BoundingBox getBounds() {
        if (coords == null || coords.isEmpty()) {
            return null;
        }

        double minLat = coords.get(0).getLat();
        double maxLat = coords.get(0).getLat();
        double minLng = coords.get(0).getLng();
        double maxLng = coords.get(0).getLng();

        for (Coordinate coord : coords) {
            if (coord.getLat() < minLat)
                minLat = coord.getLat();
            if (coord.getLat() > maxLat)
                maxLat = coord.getLat();
            if (coord.getLng() < minLng)
                minLng = coord.getLng();
            if (coord.getLng() > maxLng)
                maxLng = coord.getLng();
        }

        return new BoundingBox(minLat, minLng, maxLat, maxLng);
    }
}
