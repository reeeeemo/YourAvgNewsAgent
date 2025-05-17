import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import TextareaAutosize from 'react-textarea-autosize';
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
      const response = await fetch('/query', {
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
      const data = await response.json();
      return data.response;
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
          {messages.map((message, index) => {
            const bubbleClass = message.role === 'user' ? 'message-blurb' : 'response-blurb'

            const MarkdownElement = (Tag) => ({ node, ...props}) => (
              <Tag {...props}/>
            );
            
            return (
            <div key={index} className={bubbleClass}>
              <ReactMarkdown rehypePlugins={[rehypeSanitize]}
              key={index}
              components={{
                p: MarkdownElement('p'),
                ul: MarkdownElement('ul'),
                ol: MarkdownElement('ol'),
                li: MarkdownElement('li'),
                h1: MarkdownElement('h1'),
                h2: MarkdownElement('h2'),
                h3: MarkdownElement('h3')
              }}>
              {message.content}
              </ReactMarkdown>
            </div>
            );
          })}
        </div>
        <div className="user-response-box">
          <TextareaAutosize type="text" id="query" name="query" 
          className="input-response"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && !loading  && handleSendMessage()}
          minRows={1}
          maxRows={6}/>
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
