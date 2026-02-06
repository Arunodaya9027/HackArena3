package com.geoclear.api.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

/**
 * Response containing processed geometry results
 */
public class GeometryResponse {

    private List<DisplacementResult> results;

    @JsonProperty("total_conflicts")
    private int totalConflicts;

    @JsonProperty("total_displaced")
    private int totalDisplaced;

    @JsonProperty("processing_summary")
    private Map<String, Object> processingSummary;

    public GeometryResponse() {
    }

    public GeometryResponse(List<DisplacementResult> results, int totalConflicts,
            int totalDisplaced, Map<String, Object> processingSummary) {
        this.results = results;
        this.totalConflicts = totalConflicts;
        this.totalDisplaced = totalDisplaced;
        this.processingSummary = processingSummary;
    }

    // Getters and Setters
    public List<DisplacementResult> getResults() {
        return results;
    }

    public void setResults(List<DisplacementResult> results) {
        this.results = results;
    }

    public int getTotalConflicts() {
        return totalConflicts;
    }

    public void setTotalConflicts(int totalConflicts) {
        this.totalConflicts = totalConflicts;
    }

    public int getTotalDisplaced() {
        return totalDisplaced;
    }

    public void setTotalDisplaced(int totalDisplaced) {
        this.totalDisplaced = totalDisplaced;
    }

    public Map<String, Object> getProcessingSummary() {
        return processingSummary;
    }

    public void setProcessingSummary(Map<String, Object> processingSummary) {
        this.processingSummary = processingSummary;
    }

    @Override
    public String toString() {
        return "GeometryResponse{" +
                "resultsCount=" + (results != null ? results.size() : 0) +
                ", totalConflicts=" + totalConflicts +
                ", totalDisplaced=" + totalDisplaced +
                ", processingSummary=" + processingSummary +
                '}';
    }
}
