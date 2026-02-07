package com.geoclear.api.service;

import com.geoclear.api.model.FeatureInput;
import com.geoclear.api.model.FeaturePriority;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * Service for ingesting WKT data from files
 */
@Service
public class WktIngestionService {

    private static final Logger logger = LoggerFactory.getLogger(WktIngestionService.class);

    /**
     * Load WKT features from a file
     * Handles both single-line and multi-line LINESTRING entries
     * 
     * @param filePath        Path to WKT file
     * @param defaultPriority Default priority to assign to features
     * @return List of FeatureInput
     */
    public List<FeatureInput> loadWktFile(String filePath, FeaturePriority defaultPriority) throws IOException {
        logger.info("Loading WKT file: {}", filePath);

        File file = new File(filePath);
        if (!file.exists()) {
            throw new IOException("WKT file not found: " + filePath);
        }

        String content = FileUtils.readFileToString(file, StandardCharsets.UTF_8);
        List<FeatureInput> features = new ArrayList<>();

        // Parse multi-line WKT entries
        StringBuilder currentWkt = new StringBuilder();
        int featureId = 1;

        String[] lines = content.split("\n");

        for (String line : lines) {
            line = line.trim();

            if (line.isEmpty()) {
                continue;
            }

            // Start of new WKT entry
            if (line.startsWith("LINESTRING")) {
                // Save previous WKT if exists
                if (currentWkt.length() > 0) {
                    String wkt = normalizeWkt(currentWkt.toString());
                    if (isValidWkt(wkt)) {
                        String id = generateFeatureId(defaultPriority, featureId++);
                        features.add(new FeatureInput(id, wkt, defaultPriority));
                    }
                    currentWkt.setLength(0);
                }
                currentWkt.append(line);
            } else {
                // Continuation of current WKT (multi-line entry)
                currentWkt.append(" ").append(line);
            }
        }

        // Don't forget the last entry
        if (currentWkt.length() > 0) {
            String wkt = normalizeWkt(currentWkt.toString());
            if (isValidWkt(wkt)) {
                String id = generateFeatureId(defaultPriority, featureId++);
                features.add(new FeatureInput(id, wkt, defaultPriority));
            }
        }

        logger.info("Loaded {} features from WKT file", features.size());
        return features;
    }

    /**
     * Normalize WKT string by removing extra whitespace and newlines
     */
    private String normalizeWkt(String wkt) {
        // Remove extra whitespace, newlines, and normalize spaces
        return wkt.replaceAll("\\s+", " ")
                .replaceAll("\\( ", "(")
                .replaceAll(" \\)", ")")
                .replaceAll(" ,", ",")
                .replaceAll(", ", ",")
                .trim();
    }

    /**
     * Load WKT features with mixed priorities based on heuristics
     * Handles both single-line and multi-line LINESTRING entries
     * This is a simplified approach - in real scenario, priorities would come from
     * attributes
     */
    public List<FeatureInput> loadWktFileWithPriorities(String filePath) throws IOException {
        logger.info("Loading WKT file with priority detection: {}", filePath);

        File file = new File(filePath);
        if (!file.exists()) {
            throw new IOException("WKT file not found: " + filePath);
        }

        String content = FileUtils.readFileToString(file, StandardCharsets.UTF_8);
        List<FeatureInput> features = new ArrayList<>();

        int highwayId = 1;
        int roadId = 1;

        // Parse multi-line WKT entries
        StringBuilder currentWkt = new StringBuilder();

        String[] lines = content.split("\n");

        for (String line : lines) {
            line = line.trim();

            if (line.isEmpty()) {
                continue;
            }

            // Start of new WKT entry
            if (line.startsWith("LINESTRING")) {
                // Save previous WKT if exists
                if (currentWkt.length() > 0) {
                    String wkt = normalizeWkt(currentWkt.toString());
                    if (isValidWkt(wkt)) {
                        FeaturePriority priority = detectPriority(wkt);
                        String id;
                        if (priority == FeaturePriority.P1_HIGHWAY) {
                            id = generateFeatureId(priority, highwayId++);
                        } else {
                            id = generateFeatureId(priority, roadId++);
                        }
                        features.add(new FeatureInput(id, wkt, priority));
                    }
                    currentWkt.setLength(0);
                }
                currentWkt.append(line);
            } else {
                // Continuation of current WKT (multi-line entry)
                currentWkt.append(" ").append(line);
            }
        }

        // Don't forget the last entry
        if (currentWkt.length() > 0) {
            String wkt = normalizeWkt(currentWkt.toString());
            if (isValidWkt(wkt)) {
                FeaturePriority priority = detectPriority(wkt);
                String id;
                if (priority == FeaturePriority.P1_HIGHWAY) {
                    id = generateFeatureId(priority, highwayId++);
                } else {
                    id = generateFeatureId(priority, roadId++);
                }
                features.add(new FeatureInput(id, wkt, priority));
            }
        }

        logger.info("Loaded {} features (highways + roads) from WKT file", features.size());
        return features;
    }

    /**
     * Intelligent multi-factor heuristic to detect feature priority
     * Uses geometric properties to classify into 13 distinct categories
     * 
     * Classification factors:
     * - Coordinate count (complexity)
     * - Path length (geometric extent)
     * - Curvature (straightness vs loops)
     * - Coordinate density (detail level)
     * - Bounding box aspect ratio
     */
    private FeaturePriority detectPriority(String wkt) {
        try {
            // Extract coordinates from WKT
            String coordsStr = wkt.replaceAll("LINESTRING\\s*\\(", "").replaceAll("\\)", "").trim();
            String[] coordPairs = coordsStr.split(",");

            int coordCount = coordPairs.length;

            // Parse coordinates for geometric analysis
            double[][] coords = new double[coordCount][2];
            for (int i = 0; i < coordCount; i++) {
                String[] xy = coordPairs[i].trim().split("\\s+");
                if (xy.length >= 2) {
                    coords[i][0] = Double.parseDouble(xy[0]);
                    coords[i][1] = Double.parseDouble(xy[1]);
                }
            }

            // Calculate geometric metrics
            double pathLength = calculatePathLength(coords);
            double curvature = calculateCurvature(coords);
            double[] bbox = getBoundingBox(coords);
            double aspectRatio = (bbox[2] - bbox[0]) / Math.max(bbox[3] - bbox[1], 0.001);

            // Decision tree classification

            // P1: Critical Infrastructure
            if (coordCount > 20 && pathLength > 500 && curvature < 0.1) {
                return FeaturePriority.P1_HIGHWAY; // Long, straight, complex = Highway
            }

            if (coordCount > 15 && Math.abs(aspectRatio - 1.0) < 0.3 && pathLength > 300) {
                return FeaturePriority.P1_RAILWAY; // Long, balanced, moderate complexity = Railway
            }

            if (coordCount > 30 && curvature > 0.3) {
                return FeaturePriority.P1_RIVER; // Very complex, curvy = River
            }

            // P2: Major Roads
            if (coordCount > 12 && pathLength > 200 && curvature < 0.2) {
                return FeaturePriority.P2_MAIN_ROAD; // Moderately long, straight = Main Road
            }

            // P3: Local Streets
            if (coordCount > 8 && pathLength > 100 && curvature < 0.25) {
                return FeaturePriority.P3_LOCAL_ROAD; // Medium length, fairly straight = Local Road
            }

            if (coordCount > 5 && pathLength > 50) {
                return FeaturePriority.P3_STREET; // Short-medium length = Street
            }

            // P4: Structures
            if (coordCount > 6 && isClosedLoop(coords)) {
                return FeaturePriority.P4_BUILDING; // Closed loop = Building
            }

            if (coordCount > 10 && curvature > 0.4 && pathLength < 300) {
                return FeaturePriority.P4_PARK; // Curvy, medium size = Park boundary
            }

            // P5: Decorative Elements
            if (coordCount <= 3 && pathLength < 20) {
                return FeaturePriority.P5_ICON; // Very short, simple = Icon marker
            }

            if (coordCount <= 4 && pathLength < 30) {
                return FeaturePriority.P5_LABEL; // Short, simple = Label marker
            }

            // Default fallback
            return FeaturePriority.P3_STREET; // Default to street for unknown cases

        } catch (Exception e) {
            logger.warn("Error detecting priority for WKT, defaulting to P3_STREET: {}", e.getMessage());
            return FeaturePriority.P3_STREET;
        }
    }

    /**
     * Calculate total path length from coordinates
     */
    private double calculatePathLength(double[][] coords) {
        double totalLength = 0.0;
        for (int i = 1; i < coords.length; i++) {
            double dx = coords[i][0] - coords[i - 1][0];
            double dy = coords[i][1] - coords[i - 1][1];
            totalLength += Math.sqrt(dx * dx + dy * dy);
        }
        return totalLength;
    }

    /**
     * Calculate average curvature (0 = straight, higher = more curved)
     * Uses angle changes between consecutive segments
     */
    private double calculateCurvature(double[][] coords) {
        if (coords.length < 3)
            return 0.0;

        double totalAngleChange = 0.0;
        int angleCount = 0;

        for (int i = 1; i < coords.length - 1; i++) {
            // Calculate vectors
            double v1x = coords[i][0] - coords[i - 1][0];
            double v1y = coords[i][1] - coords[i - 1][1];
            double v2x = coords[i + 1][0] - coords[i][0];
            double v2y = coords[i + 1][1] - coords[i][1];

            // Calculate angle between vectors
            double dot = v1x * v2x + v1y * v2y;
            double mag1 = Math.sqrt(v1x * v1x + v1y * v1y);
            double mag2 = Math.sqrt(v2x * v2x + v2y * v2y);

            if (mag1 > 0.001 && mag2 > 0.001) {
                double cosAngle = dot / (mag1 * mag2);
                // Clamp to [-1, 1] to handle floating point errors
                cosAngle = Math.max(-1.0, Math.min(1.0, cosAngle));
                double angle = Math.acos(cosAngle);
                totalAngleChange += angle;
                angleCount++;
            }
        }

        return angleCount > 0 ? totalAngleChange / angleCount : 0.0;
    }

    /**
     * Check if path forms a closed loop
     */
    private boolean isClosedLoop(double[][] coords) {
        if (coords.length < 4)
            return false;

        double dx = coords[0][0] - coords[coords.length - 1][0];
        double dy = coords[0][1] - coords[coords.length - 1][1];
        double distance = Math.sqrt(dx * dx + dy * dy);

        // Consider closed if start/end are within 1 unit
        return distance < 1.0;
    }

    /**
     * Get bounding box [minX, minY, maxX, maxY]
     */
    private double[] getBoundingBox(double[][] coords) {
        double minX = Double.MAX_VALUE, minY = Double.MAX_VALUE;
        double maxX = Double.MIN_VALUE, maxY = Double.MIN_VALUE;

        for (double[] coord : coords) {
            minX = Math.min(minX, coord[0]);
            minY = Math.min(minY, coord[1]);
            maxX = Math.max(maxX, coord[0]);
            maxY = Math.max(maxY, coord[1]);
        }

        return new double[] { minX, minY, maxX, maxY };
    }

    /**
     * Generate feature ID based on priority
     */
    private String generateFeatureId(FeaturePriority priority, int sequence) {
        String prefix;
        switch (priority) {
            case P1_HIGHWAY:
                prefix = "highway";
                break;
            case P1_RAILWAY:
                prefix = "railway";
                break;
            case P1_RIVER:
                prefix = "river";
                break;
            case P2_MAIN_ROAD:
                prefix = "main_road";
                break;
            case P3_LOCAL_ROAD:
                prefix = "local_road";
                break;
            case P3_STREET:
                prefix = "street";
                break;
            case P4_BUILDING:
                prefix = "building";
                break;
            case P4_PARK:
                prefix = "park";
                break;
            case P5_LABEL:
                prefix = "label";
                break;
            case P5_ICON:
                prefix = "icon";
                break;
            case P5_OVERLAP_AREA:
                prefix = "overlap";
                break;
            default:
                prefix = "feature";
                break;
        }
        return String.format("%s_%03d", prefix, sequence);
    }

    /**
     * Validate WKT string
     * Checks for proper LINESTRING format with balanced parentheses
     */
    public boolean isValidWkt(String wkt) {
        if (wkt == null || wkt.trim().isEmpty()) {
            return false;
        }

        String normalized = wkt.trim();

        // Must start with LINESTRING
        if (!normalized.startsWith("LINESTRING")) {
            return false;
        }

        // Must contain opening and closing parentheses
        if (!normalized.contains("(") || !normalized.contains(")")) {
            return false;
        }

        // Check balanced parentheses
        int openCount = 0;
        int closeCount = 0;
        for (char c : normalized.toCharArray()) {
            if (c == '(')
                openCount++;
            if (c == ')')
                closeCount++;
        }

        if (openCount != closeCount || openCount == 0) {
            return false;
        }

        // Must end with closing parenthesis (after trimming)
        if (!normalized.trim().endsWith(")")) {
            return false;
        }

        // Extract coordinates part
        int startIdx = normalized.indexOf('(');
        int endIdx = normalized.lastIndexOf(')');

        if (startIdx >= endIdx) {
            return false;
        }

        String coordsPart = normalized.substring(startIdx + 1, endIdx).trim();

        // Must have at least 2 coordinate pairs for a valid LINESTRING
        String[] coords = coordsPart.split(",");
        if (coords.length < 2) {
            return false;
        }

        // Check that each coordinate pair has 2 numbers (x y)
        for (String coord : coords) {
            String[] parts = coord.trim().split("\\s+");
            if (parts.length < 2) {
                return false;
            }
            // Validate that they are numbers
            try {
                Double.parseDouble(parts[0]);
                Double.parseDouble(parts[1]);
            } catch (NumberFormatException e) {
                return false;
            }
        }

        return true;
    }
}
