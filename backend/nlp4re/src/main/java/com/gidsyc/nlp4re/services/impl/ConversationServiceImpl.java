package com.gidsyc.nlp4re.services.impl;

import com.gidsyc.nlp4re.dto.chat.ConversationRequest;
import com.gidsyc.nlp4re.dto.chat.ConversationResponse;
import com.gidsyc.nlp4re.dto.chat.MessageRequest;
import com.gidsyc.nlp4re.dto.chat.MessageResponse;
import com.gidsyc.nlp4re.exceptions.ResourceNotFoundException;
import com.gidsyc.nlp4re.exceptions.UnauthorizedException;
import com.gidsyc.nlp4re.models.Conversation;
import com.gidsyc.nlp4re.models.Message;
import com.gidsyc.nlp4re.models.User;
import com.gidsyc.nlp4re.repositories.ConversationRepository;
import com.gidsyc.nlp4re.repositories.MessageRepository;
import com.gidsyc.nlp4re.repositories.UserRepository;
import com.gidsyc.nlp4re.services.ConversationService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@Transactional
public class ConversationServiceImpl implements ConversationService {

    private final ConversationRepository conversationRepository;
    private final MessageRepository messageRepository;
    private final UserRepository userRepository;

    public ConversationServiceImpl(ConversationRepository conversationRepository,
                                   MessageRepository messageRepository,
                                   UserRepository userRepository) {
        this.conversationRepository = conversationRepository;
        this.messageRepository = messageRepository;
        this.userRepository = userRepository;
    }

    @Override
    public List<ConversationResponse> getConversations(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("Usuario no encontrado"));
        return conversationRepository.findAllByUserIdOrderByCreatedAtDesc(user.getId()).stream()
                .map(this::mapToConversationResponse)
                .toList();
    }

    @Override
    public ConversationResponse createConversation(String username, ConversationRequest request) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("Usuario no encontrado"));
        Conversation conversation = new Conversation();
        conversation.setUser(user);
        conversation.setTitle(request.title() == null || request.title().isBlank() ? "Nueva Conversación" : request.title());
        Conversation saved = conversationRepository.save(conversation);
        return mapToConversationResponse(saved);
    }

    @Override
    public List<MessageResponse> getMessages(UUID conversationId, String username) {
        Conversation conversation = getValidatedConversation(conversationId, username);
        return messageRepository.findAllByConversationIdOrderByCreatedAtAsc(conversation.getId()).stream()
                .map(this::mapToMessageResponse)
                .toList();
    }

    @Override
    public MessageResponse addMessage(UUID conversationId, String username, MessageRequest request) {
        Conversation conversation = getValidatedConversation(conversationId, username);
        Message message = new Message();
        message.setConversation(conversation);
        message.setSender(request.sender());
        message.setContent(request.content());
        Message saved = messageRepository.save(message);
        return mapToMessageResponse(saved);
    }

    @Override
    public void deleteConversation(UUID conversationId, String username) {
        Conversation conversation = getValidatedConversation(conversationId, username);
        conversationRepository.delete(conversation);
    }

    private Conversation getValidatedConversation(UUID conversationId, String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("Usuario no encontrado"));
        Conversation conversation = conversationRepository.findById(conversationId)
                .orElseThrow(() -> new ResourceNotFoundException("Conversación no encontrada"));
        if (!conversation.getUser().getId().equals(user.getId())) {
            throw new UnauthorizedException("No está autorizado para acceder a esta conversación");
        }
        return conversation;
    }

    private ConversationResponse mapToConversationResponse(Conversation conv) {
        return new ConversationResponse(conv.getId(), conv.getTitle(), conv.getCreatedAt());
    }

    private MessageResponse mapToMessageResponse(Message msg) {
        return new MessageResponse(msg.getId(), msg.getSender(), msg.getContent(), msg.getCreatedAt());
    }
}
