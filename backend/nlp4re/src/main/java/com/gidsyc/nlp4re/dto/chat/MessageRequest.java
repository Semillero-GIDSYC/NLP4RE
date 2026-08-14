package com.gidsyc.nlp4re.dto.chat;

public record MessageRequest(
    String sender,
    String content
) {}
