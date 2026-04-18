package com.aiarchitect.api.exception;

public class AgentCommunicationException extends RuntimeException {
    public AgentCommunicationException(String message, Throwable cause) {
        super(message, cause);
    }
    public AgentCommunicationException(String message) {
        super(message);
    }
}
