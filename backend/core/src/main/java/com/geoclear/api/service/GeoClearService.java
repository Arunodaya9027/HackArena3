package com.geoclear.api.service;

import com.geoclear.api.client.PythonGeometryEngineClient;
import com.geoclear.api.model.GeometryRequest;
import com.geoclear.api.model.GeometryResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Main GeoClear service orchestrating the processing pipeline
 */
@Service
public class GeoClearService {

    private static final Logger logger = LoggerFactory.getLogger(GeoClearService.class);

    private final PythonGeometryEngineClient pythonClient;
    private final DepthMetadataService depthMetadataService;
    private final WktIngestionService wktIngestionService;

    public GeoClearService(PythonGeometryEngineClient pythonClient,
            DepthMetadataService depthMetadataService,
            WktIngestionService wktIngestionService) {
        this.pythonClient = pythonClient;
        this.depthMetadataService = depthMetadataService;
        this.wktIngestionService = wktIngestionService;
    }

    /**
     * Process geometry request through the full pipeline
     */
    public GeometryResponse processGeometry(GeometryRequest request) {
        logger.info("Processing geometry request with {} features", request.getFeatures().size());

        // Validate input
        validateRequest(request);

        // Send to Python geometry engine for processing
        GeometryResponse response = pythonClient.processGeometry(request);

        // Enhance with Java-side depth metadata
        response = depthMetadataService.enhanceWithDepthMetadata(response);

        logger.info("Geometry processing complete: {} conflicts, {} displaced",
                response.getTotalConflicts(), response.getTotalDisplaced());

        return response;
    }

    /**
     * Validate geometry request
     */
    private void validateRequest(GeometryRequest request) {
        if (request.getFeatures() == null || request.getFeatures().isEmpty()) {
            throw new IllegalArgumentException("Features list cannot be empty");
        }

        if (request.getMinClearance() <= 0) {
            throw new IllegalArgumentException("Min clearance must be positive");
        }

        // Validate WKT strings
        for (var feature : request.getFeatures()) {
            if (!wktIngestionService.isValidWkt(feature.getWkt())) {
                throw new IllegalArgumentException("Invalid WKT for feature: " + feature.getId());
            }
        }

        logger.debug("Request validation passed");
    }

    /**
     * Check health of dependent services
     */
    public boolean isHealthy() {
        return pythonClient.isHealthy();
    }
}
