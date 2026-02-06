package com.geoclear.api.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Metadata about a detected conflict
 */
public class ConflictMetadata {

    @JsonProperty("conflict_pair")
    private List<String> conflictPair;

    @JsonProperty("displacement_vector")
    private List<Double> displacementVector;

    @JsonProperty("overlap_amount")
    private double overlapAmount;

    @JsonProperty("z_index")
    private Integer zIndex;

    @JsonProperty("visual_depth_flag")
    private boolean visualDepthFlag;

    public ConflictMetadata() {
    }

    public ConflictMetadata(List<String> conflictPair, List<Double> displacementVector,
            double overlapAmount, Integer zIndex, boolean visualDepthFlag) {
        this.conflictPair = conflictPair;
        this.displacementVector = displacementVector;
        this.overlapAmount = overlapAmount;
        this.zIndex = zIndex;
        this.visualDepthFlag = visualDepthFlag;
    }

    // Getters and Setters
    public List<String> getConflictPair() {
        return conflictPair;
    }

    public void setConflictPair(List<String> conflictPair) {
        this.conflictPair = conflictPair;
    }

    public List<Double> getDisplacementVector() {
        return displacementVector;
    }

    public void setDisplacementVector(List<Double> displacementVector) {
        this.displacementVector = displacementVector;
    }

    public double getOverlapAmount() {
        return overlapAmount;
    }

    public void setOverlapAmount(double overlapAmount) {
        this.overlapAmount = overlapAmount;
    }

    public Integer getZIndex() {
        return zIndex;
    }

    public void setZIndex(Integer zIndex) {
        this.zIndex = zIndex;
    }

    public boolean isVisualDepthFlag() {
        return visualDepthFlag;
    }

    public void setVisualDepthFlag(boolean visualDepthFlag) {
        this.visualDepthFlag = visualDepthFlag;
    }

    @Override
    public String toString() {
        return "ConflictMetadata{" +
                "conflictPair=" + conflictPair +
                ", displacementVector=" + displacementVector +
                ", overlapAmount=" + overlapAmount +
                ", zIndex=" + zIndex +
                ", visualDepthFlag=" + visualDepthFlag +
                '}';
    }
}
