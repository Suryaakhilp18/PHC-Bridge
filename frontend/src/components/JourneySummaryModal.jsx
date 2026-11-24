import React, { useState, useEffect } from 'react';
import { Sparkles, X, CheckCircle2, History, AlertCircle, RefreshCw, Languages } from 'lucide-react';

export default function JourneySummaryModal({ referral, api, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [translation, setTranslation] = useState(null);
  const [translating, setTranslating] = useState(false);
  const [targetLang, setTargetLang] = useState('telugu');

  useEffect(() => {
    fetchSummary();
  }, [referral.id]);

  async function fetchSummary() {
    setLoading(true);
    try {
      const res = await api('/api/ai/summarize', {
        method: 'POST',
        body: JSON.stringify({ referral_id: referral.id })
      });
      setData(res);
    } catch (e) {
      console.warn('Failed journey summary', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleTranslate(lang) {
    if (!data) return;
    setTranslating(true);
    setTargetLang(lang);
    try {
      const textToTranslate = referral.outcome || referral.follow_up_note || referral.reason;
      const res = await api('/api/ai/translate', {
        method: 'POST',
        body: JSON.stringify({ text: textToTranslate, target_language: lang })
      });
      setTranslation(res);
    } catch (e) {
      console.warn('Translation failed', e);
    } finally {
      setTranslating(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal wide">
        <div className="modal-head">
          <div className="flex-row items-center gap-2">
            <div className="ai-badge-icon"><Sparkles size={20} /></div>
            <div>
              <h2>AI Patient Journey Summary</h2>
              <p>Verified historical facts and administrative continuity summary for {referral.patient_name}.</p>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={18} /></button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-muted">
            <RefreshCw className="spin mb-2" size={24} />
            <p>Analyzing referral lifecycle timeline...</p>
          </div>
        ) : data ? (
          <div className="journey-summary-body">
            <div className="ai-narrative-card">
              <div className="narrative-tag">
                <Sparkles size={14} />
                <span>AI Administrative Synthesis</span>
              </div>
              <p>{data.ai_generated_summary}</p>
            </div>

            <div className="facts-timeline-section">
              <h3>
                <History size={16} /> Documented Timeline Facts
              </h3>
              <div className="timeline-list">
                {data.timeline_facts.map((f, i) => (
                  <div key={i} className="timeline-fact-item">
                    <span className="fact-dot" />
                    <div className="fact-content">
                      <div className="flex-between">
                        <b>{f.stage}</b>
                        <small className="text-muted">{f.date}</small>
                      </div>
                      <p>{f.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {data.pending_actions && data.pending_actions.length > 0 && (
              <div className="pending-actions-card">
                <b>Pending Administrative Actions:</b>
                <ul>
                  {data.pending_actions.map((act, i) => (
                    <li key={i}>{act}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Multilingual Translation Tool */}
            <div className="translation-section">
              <div className="flex-between items-center mb-2">
                <div className="flex-row items-center gap-1">
                  <Languages size={16} className="text-teal" />
                  <b>Multilingual Follow-up Translation Aid</b>
                </div>
                <div className="flex-row gap-1">
                  <button
                    className={`chip-btn ${targetLang === 'telugu' ? 'active' : ''}`}
                    onClick={() => handleTranslate('telugu')}
                    disabled={translating}
                  >
                    Telugu (తెలుగు)
                  </button>
                  <button
                    className={`chip-btn ${targetLang === 'hindi' ? 'active' : ''}`}
                    onClick={() => handleTranslate('hindi')}
                    disabled={translating}
                  >
                    Hindi (हिंदी)
                  </button>
                </div>
              </div>

              {translation && (
                <div className="translation-result-box">
                  <small className="text-muted">Target: {translation.target_language}</small>
                  <p className="translated-text">{translation.translated_text}</p>
                  <span className="text-xs text-muted">{translation.disclaimer}</span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-6 text-center text-muted">Summary not available.</div>
        )}
      </div>
    </div>
  );
}
