package com.gidsyc.nlp4re.controllers;

import com.gidsyc.nlp4re.dto.chat.ConversationRequest;
import com.gidsyc.nlp4re.dto.chat.ConversationResponse;
import com.gidsyc.nlp4re.dto.chat.MessageRequest;
import com.gidsyc.nlp4re.dto.chat.MessageResponse;
import com.gidsyc.nlp4re.services.ConversationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@Tag(name = "Chat Conversations", description = "Endpoints para la gestion de conversaciones y mensajeria del chat")
@RestController
@RequestMapping("/api/v1/conversations")
public class ConversationController {

    private final ConversationService conversationService;

    public ConversationController(ConversationService conversationService) {
        this.conversationService = conversationService;
    }

    @GetMapping
    @Operation(summary = "Listar todas las conversaciones del usuario autenticado")
    public ResponseEntity<List<ConversationResponse>> getConversations() {
        String username = getAuthenticatedUsername();
        return ResponseEntity.ok(conversationService.getConversations(username));
    }

    @PostMapping
    @Operation(summary = "Crear una nueva conversacion")
    public ResponseEntity<ConversationResponse> createConversation(@RequestBody ConversationRequest request) {
        String username = getAuthenticatedUsername();
        return ResponseEntity.ok(conversationService.createConversation(username, request));
    }

    @GetMapping("/{id}/messages")
    @Operation(summary = "Obtener los mensajes de una conversacion")
    public ResponseEntity<List<MessageResponse>> getMessages(@PathVariable UUID id) {
        String username = getAuthenticatedUsername();
        return ResponseEntity.ok(conversationService.getMessages(id, username));
    }

    @PostMapping("/{id}/messages")
    @Operation(summary = "Agregar un mensaje a una conversacion")
    public ResponseEntity<MessageResponse> addMessage(@PathVariable UUID id, @RequestBody MessageRequest request) {
        String username = getAuthenticatedUsername();
        return ResponseEntity.ok(conversationService.addMessage(id, username, request));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Eliminar una conversacion")
    public ResponseEntity<Void> deleteConversation(@PathVariable UUID id) {
        String username = getAuthenticatedUsername();
        conversationService.deleteConversation(id, username);
        return ResponseEntity.noContent().build();
    }

    private String getAuthenticatedUsername() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return auth.getName();
    }
}
