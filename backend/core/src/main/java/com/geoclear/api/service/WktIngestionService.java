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
     * Simple heuristic to detect priority based on feature length
     */
    private FeaturePriority detectPriority(String wkt) {
        // Count commas to estimate number of coordinates
        int coordinateCount = wkt.split(",").length;

        // Longer features (more coordinates) assumed to be highways
        return coordinateCount > 10 ? FeaturePriority.P1_HIGHWAY : FeaturePriority.P2_ROAD;
    }

    /**
     * Generate feature ID
     */
    private String generateFeatureId(FeaturePriority priority, int sequence) {
        String prefix = priority == FeaturePriority.P1_HIGHWAY ? "highway" : "road";
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
