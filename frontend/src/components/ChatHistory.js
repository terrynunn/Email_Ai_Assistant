import React from 'react';
import '../styles/ChatHistory.css';

function ChatHistory({ messages }) {
  return (
    <div className="chat-history-container">
      <h2>Chat History</h2>
      <div className="messages">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.role === 'user' ? 'user' : 'assistant'}`}
          >
            <div className="message-header">
              {message.role === 'user' ? 'You' : 'Assistant'}
            </div>
            <div className="message-content">{message.content}</div>
            <div className="message-timestamp">
              {new Date(message.timestamp).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ChatHistory; 