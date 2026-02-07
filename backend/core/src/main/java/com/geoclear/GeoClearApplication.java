package com.geoclear;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * GeoClear Backend Application
 * Main Spring Boot application for geometric displacement processing
 */
@SpringBootApplication
public class GeoClearApplication {

    public static void main(String[] args) {
        SpringApplication.run(GeoClearApplication.class, args);
        System.out.println("\n===========================================");
        System.out.println("🚀 GeoClear Backend Server Started!");
        System.out.println("📍 Port: 8085");
        System.out.println("🔗 API: http://localhost:8085/api");
        System.out.println("===========================================\n");
    }

    /**
     * Configure CORS to allow frontend requests
     */
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/api/**")
                        .allowedOrigins("*")
                        .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                        .allowedHeaders("*");
            }
        };
    }
}
