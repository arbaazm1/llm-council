import { useState, useEffect } from 'react';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isOpen,
  onClose,
}) {
  const handleDelete = (e, conversationId, conversationTitle) => {
    e.stopPropagation(); // Prevent selecting the conversation
    
    const confirmed = window.confirm(
      `Are you sure you want to delete "${conversationTitle}"?`
    );
    
    if (confirmed) {
      onDeleteConversation(conversationId);
    }
  };

  const handleSelectConversation = (id) => {
    onSelectConversation(id);
    if (onClose) {
      onClose();
    }
  };

  return (
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <h1>LLM Council</h1>
        <button className="new-conversation-btn" onClick={onNewConversation}>
          + New Conversation
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">No conversations yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId ? 'active' : ''
              }`}
              onClick={() => handleSelectConversation(conv.id)}
            >
              <div className="conversation-content">
                <div className="conversation-title">
                  {conv.processing && <span className="processing-indicator">⏳ </span>}
                  {conv.title || 'New Conversation'}
                </div>
                <div className="conversation-meta">
                  {conv.message_count} messages
                  {conv.processing && <span> • Processing...</span>}
                </div>
              </div>
              <button
                className="delete-conversation-btn"
                onClick={(e) => handleDelete(e, conv.id, conv.title)}
                title="Delete conversation"
                aria-label="Delete conversation"
              >
                🗑️
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
