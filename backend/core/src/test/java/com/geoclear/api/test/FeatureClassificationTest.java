package com.geoclear.api.test;

import com.geoclear.api.model.FeatureInput;
import com.geoclear.api.model.FeaturePriority;
import com.geoclear.api.service.WktIngestionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.stream.Collectors;

public class FeatureClassificationTest {
    private static final Logger logger = LoggerFactory.getLogger(FeatureClassificationTest.class);

    public static void main(String[] args) {
        WktIngestionService wktService = new WktIngestionService();

        // Load WKT file
        String wktPath = "C:\\__F__\\Projects\\A4\\docs\\Problem 3 - streets_ugen.wkt";
        logger.info("Loading WKT file: {}", wktPath);

        try {
            List<FeatureInput> features = wktService.loadWktFileWithPriorities(wktPath);

            // Analyze classification results
            System.out.println("\n============================================");
            System.out.println("   FEATURE CLASSIFICATION ANALYSIS");
            System.out.println("============================================\n");

            System.out.println("Total Features Loaded: " + features.size());
            System.out.println("");

            // Count by priority type
            Map<FeaturePriority, Long> counts = features.stream()
                    .collect(Collectors.groupingBy(
                            FeatureInput::getPriority,
                            Collectors.counting()));

            // Display statistics by category
            System.out.println("Classification Breakdown:");
            System.out.println("─────────────────────────────────────────");

            // Sort by priority level
            counts.entrySet().stream()
                    .sorted((e1, e2) -> {
                        int level1 = e1.getKey().getPriorityLevel();
                        int level2 = e2.getKey().getPriorityLevel();
                        return Integer.compare(level1, level2);
                    })
                    .forEach(entry -> {
                        FeaturePriority priority = entry.getKey();
                        long count = entry.getValue();
                        double percentage = (count * 100.0) / features.size();

                        System.out.printf("%-20s: %3d features (%.1f%%) - Width: %.1fpt - Level: %d\n",
                                priority.name(),
                                count,
                                percentage,
                                priority.getDisplayWidth(),
                                priority.getPriorityLevel());
                    });

            System.out.println("");

            // Show sample features from each category
            System.out.println("\nSample Features by Category:");
            System.out.println("─────────────────────────────────────────");

            counts.keySet().stream()
                    .sorted((p1, p2) -> Integer.compare(p1.getPriorityLevel(), p2.getPriorityLevel()))
                    .forEach(priority -> {
                        System.out.println("\n" + priority.name() + ":");
                        features.stream()
                                .filter(f -> f.getPriority() == priority)
                                .limit(2)
                                .forEach(f -> {
                                    String wkt = f.getWkt();
                                    int coordCount = wkt.split(",").length;
                                    String preview = wkt.length() > 80 ? wkt.substring(0, 77) + "..." : wkt;
                                    System.out.printf("  - %s (%d coords): %s\n",
                                            f.getId(), coordCount, preview);
                                });
                    });

            System.out.println("\n============================================");
            System.out.println("   GEOMETRIC ANALYSIS");
            System.out.println("============================================\n");

            // Analyze coordinate counts
            IntSummaryStatistics coordStats = features.stream()
                    .mapToInt(f -> f.getWkt().split(",").length)
                    .summaryStatistics();

            System.out.println("Coordinate Count Statistics:");
            System.out.printf("  Min:     %d\n", coordStats.getMin());
            System.out.printf("  Max:     %d\n", coordStats.getMax());
            System.out.printf("  Average: %.1f\n", coordStats.getAverage());
            System.out.println("");

            // Show most complex features
            System.out.println("Most Complex Features (by coordinate count):");
            features.stream()
                    .sorted((f1, f2) -> {
                        int c1 = f1.getWkt().split(",").length;
                        int c2 = f2.getWkt().split(",").length;
                        return Integer.compare(c2, c1);
                    })
                    .limit(5)
                    .forEach(f -> {
                        int coordCount = f.getWkt().split(",").length;
                        System.out.printf("  %s: %d coords → %s\n",
                                f.getId(), coordCount, f.getPriority().name());
                    });

            System.out.println("\n============================================");
            System.out.println("✅ Analysis Complete!");
            System.out.println("============================================\n");

        } catch (Exception e) {
            logger.error("Error loading WKT file", e);
            System.err.println("❌ Error: " + e.getMessage());
            System.exit(1);
        }
    }
}
