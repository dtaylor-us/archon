package com.aiarchitect.api.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "agent")
public class AgentClientConfig {
    private String baseUrl;
    private String internalSecret;
    private int timeoutSeconds = 120;
}
