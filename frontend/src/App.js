import React, { useState } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false)

  // message submission
  const handleSendMessage = async () => {
    if (input.trim() === '') return; // empty msg

    // add user msg
    setMessages((prevMessages) => [
      ...prevMessages,
      { role: 'user', content: input },
    ]);

    setInput('');
    setLoading(true)

    // query AI then set msg
    const response = await queryCall(input);

    setMessages((prevMessages) => [
      ...prevMessages,
      { role: 'assistant', content: response },
    ]);
    setLoading(false)
  };

  const queryCall = async (query) => {
    try {
      const response = await fetch(`http://localhost:5000/query?q=${encodeURIComponent(query)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          chat_history: messages,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.text();
      return data;
    } catch (error) {
      console.error('Error fetching data:', error);
      return 'Sorry, something went wrong.';
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="title-box">
          <h1>Your Average News Agent!</h1>
        </div>
        
        <div className="chat-box">
          {messages.map((message, index) => (
            <p key={index}
            className={message.role === 'user' ? 'message-blurb' : 'response-blurb'}>
              {message.content}
            </p>
          ))}
        </div>
        <div className="user-response-box">
          <input type="text" id="query" name="query" 
          className="input-response"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          onKeyDown={(e) => e.key === 'Enter' && !loading  && handleSendMessage()}/>
          <input type="button" id="submit" name="submit" 
          className="submit-response"
          onClick={handleSendMessage}
          disabled={loading}/>
        </div>
      </header>
    </div>
  );
}

export default App;
