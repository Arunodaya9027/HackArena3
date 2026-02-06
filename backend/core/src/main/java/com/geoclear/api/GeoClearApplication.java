package com.geoclear.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * GeoClear AI - Java Core API
 * Main Spring Boot Application
 */
@SpringBootApplication
public class GeoClearApplication {

    public static void main(String[] args) {
        SpringApplication.run(GeoClearApplication.class, args);
        System.out.println("\n" + "=".repeat(70));
        System.out.println("🚀 GeoClear AI - Java Core API Started Successfully!");
        System.out.println("📍 API Base URL: http://localhost:8080");
        System.out.println("📍 Health Check: http://localhost:8080/api/health");
        System.out.println("📍 Process Geometry: POST http://localhost:8080/api/geoclear/process");
        System.out.println("=".repeat(70) + "\n");
    }
}
