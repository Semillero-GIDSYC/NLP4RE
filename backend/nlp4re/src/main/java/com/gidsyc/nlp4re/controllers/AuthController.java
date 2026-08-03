package com.gidsyc.nlp4re.controllers;

import com.gidsyc.nlp4re.dto.auth.AuthResponse;
import com.gidsyc.nlp4re.dto.auth.LoginRequest;
import com.gidsyc.nlp4re.dto.auth.RegisterRequest;
import com.gidsyc.nlp4re.dto.user.UserResponse;
import com.gidsyc.nlp4re.security.JwtTokenProvider;
import com.gidsyc.nlp4re.services.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.Collections;
import java.util.List;

@Tag(name = "Authentication", description = "Endpoints para el registro, login y perfil del usuario")
@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final UserService userService;
    private final JwtTokenProvider tokenProvider;

    public AuthController(AuthenticationManager authenticationManager, UserService userService, JwtTokenProvider tokenProvider) {
        this.authenticationManager = authenticationManager;
        this.userService = userService;
        this.tokenProvider = tokenProvider;
    }

    @PostMapping("/register")
    @Operation(summary = "Registrar un nuevo usuario")
    public ResponseEntity<?> register(@RequestBody RegisterRequest request) {
        try {
            UserResponse response = userService.registerUser(request.username(), request.email(), request.password());
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @PostMapping("/login")
    @Operation(summary = "Autenticar un usuario y obtener un token JWT")
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        try {
            Authentication authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(request.username(), request.password())
            );

            SecurityContextHolder.getContext().setAuthentication(authentication);
            String jwt = tokenProvider.generateToken(authentication);

            org.springframework.security.core.userdetails.User userDetails = 
                    (org.springframework.security.core.userdetails.User) authentication.getPrincipal();
            
            UserResponse user = userService.getUserByUsername(userDetails.getUsername());
            List<String> roles = Collections.emptyList();
            if (userDetails.getAuthorities() != null) {
                roles = userDetails.getAuthorities().stream()
                        .map(GrantedAuthority::getAuthority)
                        .toList();
            }

            return ResponseEntity.ok(new AuthResponse(jwt, user.username(), user.email(), roles));
        } catch (Exception e) {
            return ResponseEntity.status(401).body("Credenciales invalidas");
        }
    }

    @GetMapping("/me")
    @Operation(summary = "Obtener el perfil del usuario autenticado actual")
    public ResponseEntity<?> me() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated() || authentication.getPrincipal().equals("anonymousUser")) {
            return ResponseEntity.status(401).body("No autorizado");
        }

        org.springframework.security.core.userdetails.User userDetails = 
                (org.springframework.security.core.userdetails.User) authentication.getPrincipal();

        UserResponse response = userService.getUserByUsername(userDetails.getUsername());
        return ResponseEntity.ok(response);
    }
}