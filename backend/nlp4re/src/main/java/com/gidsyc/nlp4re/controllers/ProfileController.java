package com.gidsyc.nlp4re.controllers;

import com.gidsyc.nlp4re.dto.auth.AuthResponse;
import com.gidsyc.nlp4re.dto.user.UpdateProfileRequest;
import com.gidsyc.nlp4re.dto.user.UserResponse;
import com.gidsyc.nlp4re.security.JwtTokenProvider;
import com.gidsyc.nlp4re.services.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

@Tag(name = "Profile", description = "Endpoints para que el usuario autenticado gestione su propio perfil")
@RestController
@RequestMapping("/api/v1/users/me")
public class ProfileController {

    private final UserService userService;
    private final JwtTokenProvider tokenProvider;

    public ProfileController(UserService userService, JwtTokenProvider tokenProvider) {
        this.userService = userService;
        this.tokenProvider = tokenProvider;
    }

    @GetMapping
    @Operation(summary = "Obtener el perfil del usuario autenticado")
    public ResponseEntity<UserResponse> getProfile() {
        return ResponseEntity.ok(userService.getUserByUsername(getAuthenticatedUsername()));
    }

    @PutMapping
    @Operation(summary = "Actualizar el username y el correo del usuario autenticado")
    public ResponseEntity<AuthResponse> updateProfile(@RequestBody UpdateProfileRequest request) {
        UserResponse updated = userService.updateProfile(getAuthenticatedUsername(), request);
        String newToken = tokenProvider.generateToken(updated.username());
        return ResponseEntity.ok(new AuthResponse(newToken, updated.username(), updated.email(), updated.roles()));
    }

    @DeleteMapping
    @Operation(summary = "Desactivar la cuenta del usuario autenticado")
    public ResponseEntity<Void> deactivateAccount() {
        userService.deactivateAccount(getAuthenticatedUsername());
        return ResponseEntity.noContent().build();
    }

    private String getAuthenticatedUsername() {
        return SecurityContextHolder.getContext().getAuthentication().getName();
    }
}
