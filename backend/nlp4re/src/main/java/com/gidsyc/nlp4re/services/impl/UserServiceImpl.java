package com.gidsyc.nlp4re.services.impl;

import com.gidsyc.nlp4re.dto.user.UserResponse;
import com.gidsyc.nlp4re.models.Role;
import com.gidsyc.nlp4re.models.User;
import com.gidsyc.nlp4re.repositories.RoleRepository;
import com.gidsyc.nlp4re.repositories.UserRepository;
import com.gidsyc.nlp4re.services.UserService;
import com.gidsyc.nlp4re.dto.user.UpdateProfileRequest;
import com.gidsyc.nlp4re.exceptions.BadRequestException;
import com.gidsyc.nlp4re.exceptions.ResourceNotFoundException;


import java.util.Collections;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;

    public UserServiceImpl(UserRepository userRepository, RoleRepository roleRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public UserResponse registerUser(String username, String email, String password) {
        if (userRepository.existsByUsername(username)) {
            throw new IllegalArgumentException("El nombre de usuario ya existe.");
        }
        if (userRepository.existsByEmail(email)) {
            throw new IllegalArgumentException("El correo electronico ya existe.");
        }

        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setPassword(passwordEncoder.encode(password));

        Role userRole = roleRepository.findByName("ROLE_USER")
                .orElseThrow(() -> new RuntimeException("Error: Rol 'ROLE_USER' no encontrado."));
        user.getRoles().add(userRole);

        User savedUser = userRepository.save(user);
        return mapToUserResponse(savedUser);
    }

    @Override
    public Page<UserResponse> getAllUsers(Pageable pageable) {
        return userRepository.findAll(pageable).map(this::mapToUserResponse);
    }

    @Override
    public UserResponse getUserByUsername(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("Usuario no encontrado: " + username));
        return mapToUserResponse(user);
    }

    @Override
    public UserResponse updateProfile(String currentUsername, UpdateProfileRequest request) {
        User user = userRepository.findByUsername(currentUsername)
                .orElseThrow(() -> new ResourceNotFoundException("Usuario no encontrado"));

        String newUsername = request.username() == null ? "" : request.username().trim();
        String newEmail = request.email() == null ? "" : request.email().trim();

        if (newUsername.length() < 3 || newUsername.length() > 50) {
            throw new BadRequestException("El nombre de usuario debe tener entre 3 y 50 caracteres.");
        }
        if (newEmail.length() > 100 || !newEmail.matches("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")) {
            throw new BadRequestException("El correo electronico no es valido.");
        }
        if (!newUsername.equals(user.getUsername()) && userRepository.existsByUsername(newUsername)) {
            throw new BadRequestException("El nombre de usuario ya existe.");
        }
        if (!newEmail.equals(user.getEmail()) && userRepository.existsByEmail(newEmail)) {
            throw new BadRequestException("El correo electronico ya existe.");
        }

        user.setUsername(newUsername);
        user.setEmail(newEmail);
        return mapToUserResponse(userRepository.save(user));
    }

    @Override
    public void deactivateAccount(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("Usuario no encontrado"));
        user.setActive(false);
        userRepository.save(user);
    }

    private UserResponse mapToUserResponse(User user) {
        List<String> roles = Collections.emptyList();
        roles = user.getRoles().stream()
            .map(Role::getName)
            .toList();
        return new UserResponse(
            user.getId(),
            user.getUsername(),
            user.getEmail(),
            roles,
            user.getCreatedAt()
        );
    }
}
