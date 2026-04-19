package com.aiarchitect.api.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Configuration properties for the Agent client.
 * Maps to properties prefixed with "agent" in application configuration.
 */
@Data
@ConfigurationProperties(prefix = "agent")
public class AgentClientConfig {
    /** Base URL for the agent service */
    private String baseUrl;
    
    /** Internal secret for authentication */
    private String internalSecret;
    
    /** Request timeout in seconds (default: 120) */
    private int timeoutSeconds = 120;
}
