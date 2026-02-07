package com.geoclear.api.controller;

import com.geoclear.api.model.*;
import com.geoclear.api.service.GeoClearService;
import com.geoclear.api.service.WktIngestionService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * REST Controller for GeoClear AI API
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class GeoClearController {

    private static final Logger logger = LoggerFactory.getLogger(GeoClearController.class);

    private final GeoClearService geoClearService;
    private final WktIngestionService wktIngestionService;

    public GeoClearController(GeoClearService geoClearService,
            WktIngestionService wktIngestionService) {
        this.geoClearService = geoClearService;
        this.wktIngestionService = wktIngestionService;
    }

    /**
     * Health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "healthy");
        health.put("service", "geoclear-java-api");
        health.put("python_engine_status", geoClearService.isHealthy() ? "connected" : "disconnected");

        return ResponseEntity.ok(health);
    }

    /**
     * Python engine status check endpoint
     */
    @GetMapping("/geoclear/python-status")
    public ResponseEntity<Map<String, Object>> pythonStatus() {
        Map<String, Object> status = new HashMap<>();

        boolean isHealthy = geoClearService.isHealthy();
        status.put("python_engine_status", isHealthy ? "connected" : "disconnected");
        status.put("endpoint", "http://localhost:8010/api/geometry/process");
        status.put("health_check_url", "http://localhost:8010/api/geometry/health");

        if (isHealthy) {
            status.put("message", "Python Geometry Engine is responding");
            return ResponseEntity.ok(status);
        } else {
            status.put("message", "Python Geometry Engine is not responding");
            status.put("troubleshooting",
                    "Ensure Python server is running: cd backend/python-engine && python -m app.main");
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(status);
        }
    }

    /**
     * Main endpoint: Process geometry to resolve conflicts
     */
    @PostMapping("/geoclear/process")
    public ResponseEntity<GeometryResponse> processGeometry(
            @Valid @RequestBody GeometryRequest request) {

        logger.info("Received geometry processing request: {}", request);

        try {
            GeometryResponse response = geoClearService.processGeometry(request);
            return ResponseEntity.ok(response);

        } catch (IllegalArgumentException e) {
            logger.error("Validation error: {}", e.getMessage());
            return ResponseEntity.badRequest().build();

        } catch (Exception e) {
            logger.error("Error processing geometry", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * Endpoint: Load and process WKT file
     */
    @PostMapping("/geoclear/process-file")
    public ResponseEntity<GeometryResponse> processWktFile(
            @RequestParam String filePath,
            @RequestParam(defaultValue = "P2_ROAD") FeaturePriority defaultPriority,
            @RequestParam(defaultValue = "2.0") double minClearance) {

        logger.info("Processing WKT file: {} with priority: {}", filePath, defaultPriority);

        try {
            // Load features from file
            List<FeatureInput> features = wktIngestionService.loadWktFile(filePath, defaultPriority);

            // Create request
            GeometryRequest request = new GeometryRequest(features, minClearance);

            // Process
            GeometryResponse response = geoClearService.processGeometry(request);
            return ResponseEntity.ok(response);

        } catch (IOException e) {
            logger.error("Error reading WKT file", e);
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();

        } catch (Exception e) {
            logger.error("Error processing WKT file", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * Endpoint: Load and process WKT file with auto-detected priorities
     */
    @PostMapping("/geoclear/process-file-auto")
    public ResponseEntity<GeometryResponse> processWktFileWithAutoPriorities(
            @RequestParam String filePath,
            @RequestParam(defaultValue = "2.0") double minClearance) {

        logger.info("Processing WKT file with auto-detected priorities: {}", filePath);

        try {
            // Load features with auto-detected priorities
            List<FeatureInput> features = wktIngestionService.loadWktFileWithPriorities(filePath);

            // Create request
            GeometryRequest request = new GeometryRequest(features, minClearance);

            // Process
            GeometryResponse response = geoClearService.processGeometry(request);
            return ResponseEntity.ok(response);

        } catch (IOException e) {
            logger.error("Error reading WKT file", e);
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();

        } catch (Exception e) {
            logger.error("Error processing WKT file", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * Endpoint: Get API information
     */
    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> info() {
        Map<String, Object> info = new HashMap<>();
        info.put("name", "GeoClear AI - Java Core API");
        info.put("version", "1.0.0");
        info.put("description", "System to resolve 2D map overlaps and 3D depth confusion");

        Map<String, Object> constants = new HashMap<>();
        constants.put("P1_HIGHWAY_WIDTH", 5.0);
        constants.put("P2_ROAD_WIDTH", 3.0);
        constants.put("DEFAULT_MIN_CLEARANCE", 2.0);
        info.put("constants", constants);

        return ResponseEntity.ok(info);
    }
}
