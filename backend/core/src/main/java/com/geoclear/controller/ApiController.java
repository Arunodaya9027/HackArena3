package com.geoclear.controller;

import com.geoclear.model.*;
import com.geoclear.service.DisplacementService;
import com.geoclear.service.WktProcessingService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/**
 * REST API Controller for GeoClear displacement processing
 * Handles WKT processing, feature displacement, and route management
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ApiController {

    @Autowired
    private DisplacementService displacementService;

    @Autowired
    private WktProcessingService wktProcessingService;

    /**
     * Health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "UP");
        response.put("service", "GeoClear Backend");
        response.put("version", "1.0.0");
        response.put("timestamp", System.currentTimeMillis());
        return ResponseEntity.ok(response);
    }

    /**
     * Process WKT file content and return detailed features
     * Endpoint for wkt-details-viewer.html
     */
    @PostMapping("/wkt/process")
    public ResponseEntity<Map<String, Object>> processWkt(@RequestBody Map<String, String> request) {
        try {
            String wktContent = request.get("wktContent");
            if (wktContent == null || wktContent.trim().isEmpty()) {
                return ResponseEntity.badRequest().body(
                        createErrorResponse("WKT content is required"));
            }

            // Parse WKT and process
            WktProcessingResult result = wktProcessingService.processWktContent(wktContent);

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("features", result.getFeatures());
            response.put("metrics", result.getMetrics());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(createErrorResponse("Error processing WKT: " + e.getMessage()));
        }
    }

    /**
     * Get feature details by ID
     * Used for popup/detail views
     */
    @GetMapping("/features/{id}")
    public ResponseEntity<Map<String, Object>> getFeatureDetails(@PathVariable String id) {
        try {
            FeatureDetails details = wktProcessingService.getFeatureDetails(id);

            if (details == null) {
                return ResponseEntity.notFound().build();
            }

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("feature", details);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(createErrorResponse("Error fetching feature: " + e.getMessage()));
        }
    }

    /**
     * Process displacement algorithm
     * Original endpoint from DisplacementController
     */
    @PostMapping("/displacement")
    public ResponseEntity<Map<String, Object>> processDisplacement(@RequestBody DisplacementRequest request) {
        try {
            if (request.getFeatures() == null || request.getFeatures().isEmpty()) {
                return ResponseEntity.badRequest().body(
                        createErrorResponse("Features array is required"));
            }

            ProcessingResult result = displacementService.processDisplacement(request.getFeatures());

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("features", result.getFeatures());
            response.put("metrics", Map.of(
                    "overlapsFound", result.getOverlapsDetected(),
                    "maxDisplacement", result.getMaxDisplacementMeters(),
                    "processingTime", result.getProcessingTimeSeconds()));

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(createErrorResponse("Displacement processing error: " + e.getMessage()));
        }
    }

    /**
     * API documentation endpoint
     */
    @GetMapping("/docs")
    public ResponseEntity<Map<String, Object>> getApiDocs() {
        Map<String, Object> docs = new HashMap<>();
        docs.put("service", "GeoClear Backend API");
        docs.put("version", "1.0.0");

        List<Map<String, String>> endpoints = new ArrayList<>();
        endpoints.add(createEndpointDoc("GET", "/api/health", "Health check"));
        endpoints.add(createEndpointDoc("POST", "/api/wkt/process", "Process WKT file content"));
        endpoints.add(createEndpointDoc("GET", "/api/features/{id}", "Get feature details by ID"));
        endpoints.add(createEndpointDoc("POST", "/api/displacement", "Process displacement algorithm"));
        endpoints.add(createEndpointDoc("GET", "/api/docs", "API documentation"));

        docs.put("endpoints", endpoints);

        return ResponseEntity.ok(docs);
    }

    // Helper methods

    private Map<String, Object> createErrorResponse(String message) {
        Map<String, Object> error = new HashMap<>();
        error.put("success", false);
        error.put("error", message);
        error.put("timestamp", System.currentTimeMillis());
        return error;
    }

    private Map<String, String> createEndpointDoc(String method, String path, String description) {
        Map<String, String> doc = new HashMap<>();
        doc.put("method", method);
        doc.put("path", path);
        doc.put("description", description);
        return doc;
    }
}
