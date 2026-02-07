package com.geoclear.model;

/**
 * Bounding box (min/max lat/lng)
 */
public class BoundingBox {
    private double minLat;
    private double minLng;
    private double maxLat;
    private double maxLng;

    public BoundingBox() {
    }

    public BoundingBox(double minLat, double minLng, double maxLat, double maxLng) {
        this.minLat = minLat;
        this.minLng = minLng;
        this.maxLat = maxLat;
        this.maxLng = maxLng;
    }

    public double getMinLat() {
        return minLat;
    }

    public void setMinLat(double minLat) {
        this.minLat = minLat;
    }

    public double getMinLng() {
        return minLng;
    }

    public void setMinLng(double minLng) {
        this.minLng = minLng;
    }

    public double getMaxLat() {
        return maxLat;
    }

    public void setMaxLat(double maxLat) {
        this.maxLat = maxLat;
    }

    public double getMaxLng() {
        return maxLng;
    }

    public void setMaxLng(double maxLng) {
        this.maxLng = maxLng;
    }
}
