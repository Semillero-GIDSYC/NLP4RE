package com.gidsyc.nlp4re.dto.chat;

import java.time.LocalDateTime;
import java.util.UUID;

public record MessageResponse(
    UUID id,
    String sender,
    String content,
    LocalDateTime createdAt
) {}
