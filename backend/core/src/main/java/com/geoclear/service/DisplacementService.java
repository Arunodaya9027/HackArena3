package com.geoclear.service;

import com.geoclear.model.Coordinate;
import com.geoclear.model.Feature;
import com.geoclear.model.ProcessingResult;

import org.springframework.stereotype.Service;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Core displacement algorithm service
 * Transfers logic from frontend JavaScript to Java backend
 */
@Service
public class DisplacementService {

    private static final double MIN_CLEARANCE = 10.0; // meters
    private static final int REPULSION_ITERATIONS = 5;
    private static final double EARTH_RADIUS_M = 6371000.0; // meters

    /**
     * Main displacement algorithm
     * 
     * @param features List of geographic features
     * @return ProcessingResult with displaced features and metrics
     */
    public ProcessingResult processDisplacement(List<Feature> features) {
        long startTime = System.currentTimeMillis();

        int overlapsDetected = 0;
        int overlapsResolved = 0;
        double maxDisplacementMeters = 0.0;

        // Sort by priority (lower = higher priority, fixed first)
        List<Feature> sorted = features.stream()
                .sorted(Comparator.comparingInt(f -> f.getPriority().getValue()))
                .collect(Collectors.toList());

        // Split into fixed (priority <= 2) and moveable (priority > 2)
        List<Feature> fixed = sorted.stream()
                .filter(f -> f.getPriority().getValue() <= 2)
                .collect(Collectors.toList());

        List<Feature> moveable = sorted.stream()
                .filter(f -> f.getPriority().getValue() > 2)
                .collect(Collectors.toList());

        // Iterative repulsion algorithm
        for (int iter = 0; iter < REPULSION_ITERATIONS; iter++) {
            for (Feature mFeature : moveable) {
                if (mFeature.getCoords() == null || mFeature.getCoords().size() < 2) {
                    continue;
                }

                boolean featureMoved = false;
                List<Coordinate> newCoords = new ArrayList<>();

                // Convert model coords to service coords
                for (com.geoclear.model.Coordinate modelVertex : mFeature.getCoords()) {
                    Coordinate vertex = new Coordinate(modelVertex.getLat(), modelVertex.getLng());
                    double totalDx = 0.0;
                    double totalDy = 0.0;
                    int count = 0;

                    // Check against all fixed features
                    for (Feature fFeature : fixed) {
                        // Convert model coords to service coords
                        List<Coordinate> fCoords = convertToServiceCoords(fFeature.getCoords());
                        NearestPointResult nearest = getNearestPoint(vertex, fCoords);
                        if (nearest == null)
                            continue;

                        double requiredDistMeters = (fFeature.getWidth() / 2.0) +
                                (mFeature.getWidth() / 2.0) +
                                MIN_CLEARANCE;
                        double distMeters = getDistanceMeters(vertex, nearest.point);

                        if (distMeters < requiredDistMeters) {
                            if (iter == 0)
                                overlapsDetected++;

                            double pushDistMeters = (requiredDistMeters - distMeters) * 1.2;
                            double angle = Math.atan2(
                                    vertex.getLat() - nearest.point.getLat(),
                                    vertex.getLng() - nearest.point.getLng());

                            double pushDeg = pushDistMeters / 111111.0; // approx meters to degrees

                            totalDx += Math.sin(angle) * pushDeg;
                            totalDy += Math.cos(angle) * pushDeg;
                            count++;
                        }
                    }

                    if (count > 0) {
                        featureMoved = true;
                        overlapsResolved++;

                        double newLat = vertex.getLat() + (totalDy / count);
                        double newLng = vertex.getLng() + (totalDx / count);
                        Coordinate newVertex = new Coordinate(newLat, newLng);

                        double shiftM = getDistanceMeters(vertex, newVertex);
                        if (shiftM > maxDisplacementMeters) {
                            maxDisplacementMeters = shiftM;
                        }

                        newCoords.add(newVertex);
                    } else {
                        newCoords.add(vertex);
                    }
                }

                if (featureMoved) {
                    // Convert service coords back to model coords
                    mFeature.setCoords(convertToModelCoords(newCoords));
                    mFeature.setDisplaced(true);
                }
            }
        }

        long processingTime = System.currentTimeMillis() - startTime;

        // Combine all features
        List<Feature> allFeatures = new ArrayList<>();
        allFeatures.addAll(fixed);
        allFeatures.addAll(moveable);

        return new ProcessingResult(
                allFeatures,
                overlapsDetected,
                overlapsResolved,
                maxDisplacementMeters,
                processingTime / 1000.0);
    }

    /**
     * Find nearest point on a polyline to a given point
     */
    private NearestPointResult getNearestPoint(Coordinate point, List<Coordinate> polyline) {
        if (polyline == null || polyline.size() < 2)
            return null;

        Coordinate nearestPoint = polyline.get(0);
        double minDist = getDistanceMeters(point, nearestPoint);

        for (int i = 0; i < polyline.size() - 1; i++) {
            Coordinate projected = projectPointOnSegment(point, polyline.get(i), polyline.get(i + 1));
            double dist = getDistanceMeters(point, projected);

            if (dist < minDist) {
                minDist = dist;
                nearestPoint = projected;
            }
        }

        return new NearestPointResult(nearestPoint, minDist);
    }

    /**
     * Project point onto line segment
     */
    private Coordinate projectPointOnSegment(Coordinate p, Coordinate a, Coordinate b) {
        double dx = b.getLng() - a.getLng();
        double dy = b.getLat() - a.getLat();

        if (dx == 0 && dy == 0)
            return a;

        double t = ((p.getLng() - a.getLng()) * dx + (p.getLat() - a.getLat()) * dy) / (dx * dx + dy * dy);
        t = Math.max(0, Math.min(1, t));

        return new Coordinate(
                a.getLat() + t * dy,
                a.getLng() + t * dx);
    }

    /**
     * Calculate distance between two coordinates using Haversine formula
     */
    private double getDistanceMeters(Coordinate c1, Coordinate c2) {
        double lat1 = Math.toRadians(c1.getLat());
        double lat2 = Math.toRadians(c2.getLat());
        double dLat = lat2 - lat1;
        double dLng = Math.toRadians(c2.getLng() - c1.getLng());

        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(lat1) * Math.cos(lat2) *
                        Math.sin(dLng / 2) * Math.sin(dLng / 2);

        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return EARTH_RADIUS_M * c;
    }

    /**
     * Convert model coordinates to service coordinates
     */
    private List<Coordinate> convertToServiceCoords(List<com.geoclear.model.Coordinate> modelCoords) {
        if (modelCoords == null)
            return null;
        List<Coordinate> serviceCoords = new ArrayList<>();
        for (com.geoclear.model.Coordinate mc : modelCoords) {
            serviceCoords.add(new Coordinate(mc.getLat(), mc.getLng()));
        }
        return serviceCoords;
    }

    /**
     * Convert service coordinates to model coordinates
     */
    private List<com.geoclear.model.Coordinate> convertToModelCoords(List<Coordinate> serviceCoords) {
        if (serviceCoords == null)
            return null;
        List<com.geoclear.model.Coordinate> modelCoords = new ArrayList<>();
        for (Coordinate sc : serviceCoords) {
            modelCoords.add(new com.geoclear.model.Coordinate(sc.getLat(), sc.getLng()));
        }
        return modelCoords;
    }

    /**
     * Result of nearest point calculation
     */
    private static class NearestPointResult {
        Coordinate point;
        double distance;

        NearestPointResult(Coordinate point, double distance) {
            this.point = point;
            this.distance = distance;
        }
    }

    /**
     * Inner Coordinate class (matches model)
     */
    private static class Coordinate {
        private double lat;
        private double lng;

        Coordinate(double lat, double lng) {
            this.lat = lat;
            this.lng = lng;
        }

        double getLat() {
            return lat;
        }

        double getLng() {
            return lng;
        }
    }
}
