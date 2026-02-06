package com.geoclear.api.service;

import com.geoclear.api.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Service for managing depth metadata and Z-order assignment
 * Handles 3D visualization cues for overlapping features
 */
@Service
public class DepthMetadataService {

    private static final Logger logger = LoggerFactory.getLogger(DepthMetadataService.class);

    /**
     * Enhance geometry response with additional depth metadata
     */
    public GeometryResponse enhanceWithDepthMetadata(GeometryResponse response) {
        logger.debug("Enhancing response with depth metadata");

        // Already processed by Python engine, but we can add Java-side enhancements
        for (DisplacementResult result : response.getResults()) {
            if (result.isWasDisplaced() && result.getMetadata() != null) {
                enrichMetadata(result.getMetadata());
            }
        }

        return response;
    }

    /**
     * Enrich metadata with additional fields if needed
     */
    private void enrichMetadata(ConflictMetadata metadata) {
        // Add shadow offset calculation
        if (metadata.isVisualDepthFlag() && metadata.getZIndex() != null) {
            // Shadow offset proportional to z-index
            // This could be used by frontend for rendering
            logger.debug("Enriching metadata for z-index: {}", metadata.getZIndex());
        }
    }

    /**
     * Calculate suggested shadow offset for visualization
     */
    public double calculateShadowOffset(Integer zIndex) {
        if (zIndex == null) {
            return 0.0;
        }
        // Shadow offset in pixels - higher z-index = larger shadow
        return zIndex * 2.0;
    }

    /**
     * Determine if a feature should have depth visualization
     */
    public boolean shouldApplyDepthVisualization(DisplacementResult result) {
        return result.isWasDisplaced() &&
                result.getMetadata() != null &&
                result.getMetadata().isVisualDepthFlag();
    }

    /**
     * Get CSS class for depth rendering
     */
    public String getDepthRenderingClass(Integer zIndex) {
        if (zIndex == null) {
            return "depth-default";
        }
        return switch (zIndex) {
            case 1 -> "depth-below";
            case 2 -> "depth-above";
            case 3 -> "depth-elevated";
            default -> "depth-default";
        };
    }
}
