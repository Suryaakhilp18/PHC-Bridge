import React, { useState } from 'react';
import { Bot, Send, Sparkles, X, CheckCircle2, Database, AlertCircle, RefreshCw } from 'lucide-react';

const SUGGESTED_PROMPTS = [
  "How many referrals are awaiting hospital acknowledgement?",
  "What is our referral completion rate?",
  "Which follow-up reviews are overdue?",
  "Show workload breakdown across receiving hospitals",
  "How many back-referrals were returned to PHCs?"
];

export default function AIOperationsModal({ onClose, api }) {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: 'Hello, Administrator. I am the PHC Bridge Operations Assistant. Ask me questions regarding referral flow, facility workloads, acknowledgment latency, or pending follow-ups. All metrics are calculated directly from live database records.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSend(queryText) {
    const query = (queryText || input).trim();
    if (!query) return;

    setMessages(prev => [...prev, { sender: 'user', text: query }]);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const res = await api('/api/ai/operations-query', {
        method: 'POST',
        body: JSON.stringify({ query })
      });
      setMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          text: res.answer,
          metrics: res.supporting_metrics,
          sql: res.sql_intent
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          text: 'Unable to query database operations engine. ' + (err.message || 'Server error.')
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal wide ai-modal">
        <div className="modal-head">
          <div className="flex-row items-center gap-2">
            <div className="ai-badge-icon"><Bot size={20} /></div>
            <div>
              <h2>AI Healthcare Operations Assistant</h2>
              <p>Natural language analytics query engine backed by real database metrics.</p>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="ai-chat-body">
          <div className="ai-messages-scroll">
            {messages.map((m, i) => (
              <div key={i} className={`chat-message ${m.sender}`}>
                <div className="message-content">
                  <p>{m.text}</p>
                  {m.metrics && (
                    <div className="message-metric-tag">
                      <Database size={13} />
                      <span>Verified DB Metric: Total: {m.metrics.total_referrals} | Awaiting: {m.metrics.awaiting_acknowledgement} | Overdue: {m.metrics.overdue_followups}</span>
                    </div>
                  )}
                  {m.sql && <code className="sql-intent-pill">{m.sql}</code>}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-message ai">
                <div className="message-content loading">
                  <RefreshCw className="spin" size={16} />
                  <span>Querying database metrics...</span>
                </div>
              </div>
            )}
          </div>

          <div className="ai-prompt-suggestions">
            <small className="text-muted">Suggested inquiries:</small>
            <div className="chips-row">
              {SUGGESTED_PROMPTS.map((p, i) => (
                <button key={i} className="prompt-chip" onClick={() => handleSend(p)} disabled={loading}>
                  <Sparkles size={13} className="text-teal" />
                  <span>{p}</span>
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={e => { e.preventDefault(); handleSend(); }} className="ai-chat-input-row">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask an operational question (e.g. How many referrals are pending?)..."
              disabled={loading}
            />
            <button type="submit" className="primary-btn" disabled={loading || !input.trim()}>
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
