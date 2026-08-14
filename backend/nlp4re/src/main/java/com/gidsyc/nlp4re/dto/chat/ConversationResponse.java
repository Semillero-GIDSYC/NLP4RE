package com.gidsyc.nlp4re.dto.chat;

import java.time.LocalDateTime;
import java.util.UUID;

public record ConversationResponse(
    UUID id,
    String title,
    LocalDateTime createdAt
) {}
