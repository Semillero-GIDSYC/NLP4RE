package com.gidsyc.nlp4re.dto.user;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

public record UserResponse(UUID id, String username, String email, List<String> roles, LocalDateTime createdAt) {}
