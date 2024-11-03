import React, { useState, useEffect } from 'react';
import ChatHistory from './components/ChatHistory';
import ChatInterface from './components/ChatInterface';
import './styles/App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchChatHistory();
  }, []);

  const fetchChatHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/chat-history');
      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
  };

  const handleSendMessage = async (message) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();
      await fetchChatHistory(); // Refresh chat history after sending message
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-history">
          <ChatHistory messages={messages} />
        </div>
        <div className="chat-interface">
          <ChatInterface onSendMessage={handleSendMessage} loading={loading} />
        </div>
      </div>
    </div>
  );
}

export default App; 