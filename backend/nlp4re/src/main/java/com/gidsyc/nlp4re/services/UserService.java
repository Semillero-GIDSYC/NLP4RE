package com.gidsyc.nlp4re.services;

import com.gidsyc.nlp4re.dto.user.UserResponse;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface UserService {
    UserResponse registerUser(String username, String email, String password);
    Page<UserResponse> getAllUsers(Pageable pageable);
    UserResponse getUserByUsername(String username);
}
