import { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import PromptTemplateLibrary from './components/PromptTemplateLibrary';
import DarkModeToggle from './components/DarkModeToggle';
import { api } from './api';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isTemplateLibraryOpen, setIsTemplateLibraryOpen] = useState(false);
  const chatInputSetterRef = useRef(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Poll conversations list to update processing status
  useEffect(() => {
    // Check if any conversation is processing
    const hasProcessing = conversations.some(conv => conv.processing);
    
    if (!hasProcessing) {
      return;
    }

    // Poll every 3 seconds when there are processing conversations
    const pollInterval = setInterval(() => {
      loadConversations();
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [conversations]);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  // Poll for updates when conversation is processing
  useEffect(() => {
    if (!currentConversation || !currentConversation.processing) {
      return;
    }

    // Poll every 2 seconds
    const pollInterval = setInterval(async () => {
      try {
        const updatedConv = await api.getConversation(currentConversationId);
        setCurrentConversation(updatedConv);
        
        // Stop polling when processing is complete
        if (!updatedConv.processing) {
          clearInterval(pollInterval);
          // Refresh conversations list to update message count
          loadConversations();
        }
      } catch (error) {
        console.error('Failed to poll conversation:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [currentConversation?.processing, currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { 
          id: newConv.id, 
          created_at: newConv.created_at, 
          title: newConv.title || 'New Conversation',
          message_count: 0 
        },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      
      // Remove from conversations list
      setConversations((prev) => prev.filter((conv) => conv.id !== id));
      
      // If the deleted conversation was currently selected, clear the selection
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('Failed to delete conversation. Please try again.');
    }
  };

  const loadTemplates = async () => {
    try {
      const temps = await api.listTemplates();
      setTemplates(temps);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleCreateTemplate = async (name, body) => {
    try {
      await api.createTemplate(name, body);
      await loadTemplates();
    } catch (error) {
      console.error('Failed to create template:', error);
      alert('Failed to create template. Please try again.');
    }
  };

  const handleUpdateTemplate = async (templateId, name, body) => {
    try {
      await api.updateTemplate(templateId, name, body);
      await loadTemplates();
    } catch (error) {
      console.error('Failed to update template:', error);
      alert('Failed to update template. Please try again.');
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    try {
      await api.deleteTemplate(templateId);
      await loadTemplates();
    } catch (error) {
      console.error('Failed to delete template:', error);
      alert('Failed to delete template. Please try again.');
    }
  };

  const handleUseTemplate = (promptText) => {
    if (chatInputSetterRef.current) {
      chatInputSetterRef.current(promptText);
    }
  };

  const handleChatInputChange = (setInputFn) => {
    chatInputSetterRef.current = setInputFn;
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage1 = event.data;
              lastMsg.loading.stage1 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage2_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage2 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage2_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage2 = event.data;
              lastMsg.metadata = event.metadata;
              lastMsg.loading.stage2 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage3_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage3 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage3 = event.data;
              lastMsg.loading.stage3 = false;
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            // Reload conversations to get updated title
            loadConversations();
            break;

          case 'complete':
            // Stream complete, reload conversations list
            loadConversations();
            setIsLoading(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      {/* Mobile Navigation Buttons */}
      <button 
        className="mobile-menu-button"
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        aria-label="Toggle conversations sidebar"
      >
        {isSidebarOpen ? '✕' : '☰'}
      </button>
      <button 
        className="mobile-template-button"
        onClick={() => setIsTemplateLibraryOpen(!isTemplateLibraryOpen)}
        aria-label="Toggle templates sidebar"
      >
        {isTemplateLibraryOpen ? '✕' : '📝'}
      </button>
      
      {/* Overlay for mobile */}
      <div 
        className={`mobile-nav-overlay ${(isSidebarOpen || isTemplateLibraryOpen) ? 'active' : ''}`}
        onClick={() => {
          setIsSidebarOpen(false);
          setIsTemplateLibraryOpen(false);
        }}
      />
      
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        onInputChange={handleChatInputChange}
      />
      <PromptTemplateLibrary
        templates={templates}
        onCreateTemplate={handleCreateTemplate}
        onUpdateTemplate={handleUpdateTemplate}
        onDeleteTemplate={handleDeleteTemplate}
        onRefreshTemplates={loadTemplates}
        onUseTemplate={handleUseTemplate}
        isOpen={isTemplateLibraryOpen}
        onClose={() => setIsTemplateLibraryOpen(false)}
      />
      
      {/* Dark Mode Toggle */}
      <DarkModeToggle />
    </div>
  );
}

export default App;
