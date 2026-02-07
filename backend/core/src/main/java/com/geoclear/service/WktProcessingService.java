package com.geoclear.service;

import com.geoclear.model.*;
import org.springframework.stereotype.Service;
import java.util.*;
import java.util.regex.*;

/**
 * Service for processing WKT (Well-Known Text) files
 * Parses WKT geometry and processes features
 */
@Service
public class WktProcessingService {

    private Map<String, FeatureDetails> featureCache = new HashMap<>();

    /**
     * Process WKT content and return detailed features with metrics
     */
    public WktProcessingResult processWktContent(String wktContent) {
        List<Feature> features = parseWkt(wktContent);

        // Process displacement using DisplacementService
        DisplacementService displacementService = new DisplacementService();
        ProcessingResult result = displacementService.processDisplacement(features);

        // Calculate metrics
        Map<String, Object> metrics = new HashMap<>();
        metrics.put("totalFeatures", result.getFeatures().size());
        metrics.put("displacedCount", countDisplaced(result.getFeatures()));
        metrics.put("preservedCount", result.getFeatures().size() - countDisplaced(result.getFeatures()));
        metrics.put("overlapsFound", result.getOverlapsFound());
        metrics.put("processingTime", result.getProcessingTime() + "ms");

        // Cache features for detail retrieval
        cacheFeatures(result.getFeatures());

        return new WktProcessingResult(result.getFeatures(), metrics);
    }

    /**
     * Parse WKT content into Feature objects
     */
    private List<Feature> parseWkt(String wktContent) {
        List<Feature> features = new ArrayList<>();
        String[] lines = wktContent.split("\n");
        int featureId = 1;

        for (String line : lines) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#"))
                continue;

            Feature feature = parseWktLine(line, featureId++);
            if (feature != null) {
                features.add(feature);
            }
        }

        return features;
    }

    /**
     * Parse single WKT line
     */
    private Feature parseWktLine(String line, int id) {
        try {
            // LINESTRING pattern
            Pattern lineStringPattern = Pattern.compile(
                    "LINESTRING\\s*\\(([^)]+)\\)",
                    Pattern.CASE_INSENSITIVE);
            Matcher matcher = lineStringPattern.matcher(line);

            if (matcher.find()) {
                String coordsStr = matcher.group(1);
                List<Coordinate> coords = parseCoordinates(coordsStr);

                if (coords.size() >= 2) {
                    Feature feature = new Feature();
                    String featureId = "street_" + String.format("%03d", id);
                    String featureType = determineType(line);
                    FeaturePriority featurePriority = determinePriority(line);

                    feature.setId(featureId);
                    feature.setType(featureType);
                    feature.setPriority(featurePriority);
                    feature.setWidth(determineWidth(featurePriority));
                    feature.setColor(determineColor(featurePriority));
                    feature.setZIndex(800 - (featurePriority.ordinal() * 100));
                    feature.setCoords(coords);
                    feature.setOriginalCoords(new ArrayList<>(coords));
                    feature.setDisplaced(false);

                    return feature;
                }
            }

        } catch (Exception e) {
            System.err.println("Error parsing WKT line: " + e.getMessage());
        }

        return null;
    }

    /**
     * Parse coordinate string into Coordinate objects
     */
    private List<Coordinate> parseCoordinates(String coordsStr) {
        List<Coordinate> coords = new ArrayList<>();
        String[] points = coordsStr.trim().split(",");

        for (String point : points) {
            point = point.trim();
            String[] parts = point.split("\\s+");

            if (parts.length >= 2) {
                try {
                    double lng = Double.parseDouble(parts[0]);
                    double lat = Double.parseDouble(parts[1]);
                    coords.add(new Coordinate(lat, lng));
                } catch (NumberFormatException e) {
                    System.err.println("Invalid coordinate: " + point);
                }
            }
        }

        return coords;
    }

    /**
     * Determine feature type from line content
     */
    private String determineType(String line) {
        line = line.toLowerCase();
        if (line.contains("motorway") || line.contains("highway"))
            return "motorway";
        if (line.contains("primary"))
            return "primary";
        if (line.contains("secondary"))
            return "secondary";
        if (line.contains("tertiary"))
            return "tertiary";
        if (line.contains("residential"))
            return "residential";
        return "street";
    }

    /**
     * Determine priority based on type
     */
    private FeaturePriority determinePriority(String line) {
        String type = determineType(line);
        switch (type) {
            case "motorway":
                return FeaturePriority.P1_MOTORWAY;
            case "primary":
                return FeaturePriority.P2_PRIMARY;
            case "secondary":
                return FeaturePriority.P2_PRIMARY;
            case "tertiary":
                return FeaturePriority.P3_STREET;
            default:
                return FeaturePriority.P3_STREET;
        }
    }

    /**
     * Determine width based on priority
     */
    private int determineWidth(FeaturePriority priority) {
        switch (priority) {
            case P1_MOTORWAY:
                return 25;
            case P2_PRIMARY:
                return 18;
            case P3_STREET:
                return 12;
            case P4_BUILDING:
                return 8;
            default:
                return 5;
        }
    }

    /**
     * Determine color based on priority
     */
    private String determineColor(FeaturePriority priority) {
        switch (priority) {
            case P1_MOTORWAY:
                return "#E63946";
            case P2_PRIMARY:
                return "#F77F00";
            case P3_STREET:
                return "#06D6A0";
            case P4_BUILDING:
                return "#118AB2";
            default:
                return "#073B4C";
        }
    }

    /**
     * Count displaced features
     */
    private long countDisplaced(List<Feature> features) {
        return features.stream().filter(Feature::isDisplaced).count();
    }

    /**
     * Cache features for detail retrieval
     */
    private void cacheFeatures(List<Feature> features) {
        featureCache.clear();
        for (Feature f : features) {
            FeatureDetails details = new FeatureDetails(f);
            featureCache.put(f.getId(), details);
        }
    }

    /**
     * Get feature details by ID
     */
    public FeatureDetails getFeatureDetails(String id) {
        return featureCache.get(id);
    }
}
