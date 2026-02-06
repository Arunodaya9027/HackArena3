package com.geoclear.api.client;

import com.geoclear.api.model.GeometryRequest;
import com.geoclear.api.model.GeometryResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

/**
 * Client for communicating with Python Geometry Engine microservice
 */
@Component
public class PythonGeometryEngineClient {

    private static final Logger logger = LoggerFactory.getLogger(PythonGeometryEngineClient.class);

    private final RestTemplate restTemplate;

    @Value("${python.geometry.engine.url}")
    private String pythonEngineUrl;

    @Value("${python.geometry.engine.process.endpoint}")
    private String processEndpoint;

    public PythonGeometryEngineClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Send geometry processing request to Python engine
     */
    public GeometryResponse processGeometry(GeometryRequest request) {
        String url = pythonEngineUrl + processEndpoint;

        logger.info("Sending geometry processing request to Python engine: {}", url);
        logger.debug("Request details: {}", request);

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<GeometryRequest> entity = new HttpEntity<>(request, headers);

            ResponseEntity<GeometryResponse> response = restTemplate.postForEntity(
                    url,
                    entity,
                    GeometryResponse.class);

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                logger.info("Successfully received response from Python engine");
                logger.debug("Response: {}", response.getBody());
                return response.getBody();
            } else {
                throw new RuntimeException("Python engine returned unsuccessful status: " + response.getStatusCode());
            }

        } catch (Exception e) {
            logger.error("Error communicating with Python geometry engine", e);
            throw new RuntimeException("Failed to communicate with Python geometry engine: " + e.getMessage(), e);
        }
    }

    /**
     * Check if Python engine is healthy
     */
    public boolean isHealthy() {
        try {
            String healthUrl = pythonEngineUrl + "/health";
            ResponseEntity<String> response = restTemplate.getForEntity(healthUrl, String.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            logger.warn("Python geometry engine health check failed", e);
            return false;
        }
    }
}
