import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import './App.css';
import "./Terminal.css"

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false)

  const baseUrl = process.env.NODE_ENV === 'development' ? 'http://localhost:5000' : '';

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
      const response = await fetch(`${baseUrl}/query`, {
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
    <main className="terminal">
      <header>
        <h1>$ Your Average News Agent<span className="cursor"/> </h1>
        <p>Ask me anything about today's headlines! </p>
      </header>

      <div className="prompt">
        {messages.map((message, index) => {
          const bubbleClass = message.role === 'user' ? 'prompt' : 'article-card'

          const MarkdownElement = (Tag) => ({ node, ...props }) => (
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

      <form onSubmit={(e) => {
        e.preventDefault();
        if (!loading) handleSendMessage();
      }} className="terminal-form">
        <span className="prompt">$</span>
        <input
        type="text"
        placeholder="e.g., Latest on MCP Agents"
        value={input}
        onChange={e => setInput(e.target.value)}
        autoFocus
        disabled={loading}
        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && !loading && handleSendMessage()}
        />
       </form>
    </main>
  );
}

export default App;
