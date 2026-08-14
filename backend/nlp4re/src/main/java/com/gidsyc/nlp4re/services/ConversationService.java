package com.gidsyc.nlp4re.services;

import com.gidsyc.nlp4re.dto.chat.ConversationRequest;
import com.gidsyc.nlp4re.dto.chat.ConversationResponse;
import com.gidsyc.nlp4re.dto.chat.MessageRequest;
import com.gidsyc.nlp4re.dto.chat.MessageResponse;

import java.util.List;
import java.util.UUID;

public interface ConversationService {
    List<ConversationResponse> getConversations(String username);
    ConversationResponse createConversation(String username, ConversationRequest request);
    List<MessageResponse> getMessages(UUID conversationId, String username);
    MessageResponse addMessage(UUID conversationId, String username, MessageRequest request);
    void deleteConversation(UUID conversationId, String username);
}
