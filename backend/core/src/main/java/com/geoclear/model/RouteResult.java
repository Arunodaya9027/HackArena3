package com.geoclear.model;

import java.util.List;

/**
 * Route calculation result
 */
public class RouteResult {
    private List<Coordinate> path;
    private double distanceMeters;
    private double durationSeconds;

    public RouteResult(List<Coordinate> path, double distanceMeters, double durationSeconds) {
        this.path = path;
        this.distanceMeters = distanceMeters;
        this.durationSeconds = durationSeconds;
    }

    public List<Coordinate> getPath() {
        return path;
    }

    public void setPath(List<Coordinate> path) {
        this.path = path;
    }

    public double getDistanceMeters() {
        return distanceMeters;
    }

    public void setDistanceMeters(double distanceMeters) {
        this.distanceMeters = distanceMeters;
    }

    public double getDurationSeconds() {
        return durationSeconds;
    }

    public void setDurationSeconds(double durationSeconds) {
        this.durationSeconds = durationSeconds;
    }
}
