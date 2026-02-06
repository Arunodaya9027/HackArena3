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
     * Each line should contain a LINESTRING WKT
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

        List<String> lines = FileUtils.readLines(file, StandardCharsets.UTF_8);
        List<FeatureInput> features = new ArrayList<>();

        int featureId = 1;
        for (String line : lines) {
            line = line.trim();
            if (line.isEmpty() || !line.startsWith("LINESTRING")) {
                continue;
            }

            String id = generateFeatureId(defaultPriority, featureId++);
            FeatureInput feature = new FeatureInput(id, line, defaultPriority);
            features.add(feature);
        }

        logger.info("Loaded {} features from WKT file", features.size());
        return features;
    }

    /**
     * Load WKT features with mixed priorities based on heuristics
     * This is a simplified approach - in real scenario, priorities would come from
     * attributes
     */
    public List<FeatureInput> loadWktFileWithPriorities(String filePath) throws IOException {
        logger.info("Loading WKT file with priority detection: {}", filePath);

        File file = new File(filePath);
        if (!file.exists()) {
            throw new IOException("WKT file not found: " + filePath);
        }

        List<String> lines = FileUtils.readLines(file, StandardCharsets.UTF_8);
        List<FeatureInput> features = new ArrayList<>();

        int highwayId = 1;
        int roadId = 1;

        for (String line : lines) {
            line = line.trim();
            if (line.isEmpty() || !line.startsWith("LINESTRING")) {
                continue;
            }

            // Simple heuristic: longer features are highways
            // In real scenario, this would come from attributes
            FeaturePriority priority = detectPriority(line);

            String id;
            if (priority == FeaturePriority.P1_HIGHWAY) {
                id = generateFeatureId(priority, highwayId++);
            } else {
                id = generateFeatureId(priority, roadId++);
            }

            FeatureInput feature = new FeatureInput(id, line, priority);
            features.add(feature);
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
     */
    public boolean isValidWkt(String wkt) {
        return wkt != null &&
                !wkt.trim().isEmpty() &&
                wkt.trim().startsWith("LINESTRING") &&
                wkt.contains("(") &&
                wkt.contains(")");
    }
}
