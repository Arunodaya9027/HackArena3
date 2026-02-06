package com.geoclear.api.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * Input feature with WKT geometry
 */
public class FeatureInput {

    @NotBlank(message = "Feature ID is required")
    private String id;

    @NotBlank(message = "WKT geometry is required")
    private String wkt;

    @NotNull(message = "Priority is required")
    private FeaturePriority priority;

    public FeatureInput() {
    }

    public FeatureInput(String id, String wkt, FeaturePriority priority) {
        this.id = id;
        this.wkt = wkt;
        this.priority = priority;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getWkt() {
        return wkt;
    }

    public void setWkt(String wkt) {
        this.wkt = wkt;
    }

    public FeaturePriority getPriority() {
        return priority;
    }

    public void setPriority(FeaturePriority priority) {
        this.priority = priority;
    }

    @Override
    public String toString() {
        return "FeatureInput{" +
                "id='" + id + '\'' +
                ", priority=" + priority +
                ", wkt='" + (wkt.length() > 50 ? wkt.substring(0, 50) + "..." : wkt) + '\'' +
                '}';
    }
}
