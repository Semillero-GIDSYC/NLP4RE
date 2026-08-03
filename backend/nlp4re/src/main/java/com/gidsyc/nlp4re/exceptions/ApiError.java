package com.gidsyc.nlp4re.exceptions;

import org.springframework.http.HttpStatus;
import java.time.LocalDateTime;

public record ApiError(
    LocalDateTime timestamp,
    int status,
    String error,
    String message,
    String path
) {
    public ApiError(HttpStatus status, String message, String path) {
        this(LocalDateTime.now(), status.value(), status.getReasonPhrase(), message, path);
    }
}
