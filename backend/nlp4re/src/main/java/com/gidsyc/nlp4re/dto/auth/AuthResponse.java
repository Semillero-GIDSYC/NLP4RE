package com.gidsyc.nlp4re.dto.auth;

import java.util.List;

public record AuthResponse(String token, String username, String email, List<String> roles) {}
