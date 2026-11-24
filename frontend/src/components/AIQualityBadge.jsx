import React, { useState } from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, RefreshCw, ChevronRight } from 'lucide-react';

export default function AIQualityBadge({ form, api, onApplySuggestion }) {
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [expanded, setExpanded] = useState(false);

  async function runQualityReview() {
    if (!form.reason || form.reason.length < 3) return;
    setAnalyzing(true);
    setExpanded(true);
    try {
      const data = await api('/api/ai/quality-check', {
        method: 'POST',
        body: JSON.stringify({
          reason: form.reason,
          priority: form.priority,
          destination: form.destination,
          age: parseInt(form.age || 30),
          sex: form.sex
        })
      });
      setResult(data);
    } catch (e) {
      console.warn('AI quality review unavailable', e);
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="ai-quality-card">
      <div className="quality-header">
        <div className="flex-row items-center gap-2">
          <Sparkles className="text-teal" size={17} />
          <b>AI Referral Quality Assistant</b>
        </div>
        <button
          type="button"
          className="secondary-btn small-btn"
          onClick={runQualityReview}
          disabled={analyzing || !form.reason || form.reason.length < 3}
        >
          {analyzing ? <RefreshCw className="spin" size={14} /> : 'Review Draft Quality'}
        </button>
      </div>

      {expanded && result && (
        <div className="quality-content">
          <div className="quality-score-bar">
            <span>Quality Completeness Score:</span>
            <strong className={result.score >= 80 ? 'text-green' : result.score >= 60 ? 'text-amber' : 'text-rose'}>
              {result.score}/100
            </strong>
          </div>
          <p className="clarity-text">{result.clarity_assessment}</p>

          {result.missing_fields && result.missing_fields.length > 0 && (
            <div className="quality-missing-box">
              <div className="flex-row items-center gap-1 text-amber">
                <AlertTriangle size={14} />
                <b>Noticeable Missing Context:</b>
              </div>
              <ul>
                {result.missing_fields.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}

          {result.suggested_wording && (
            <div className="suggested-wording-box">
              <small className="text-muted">Suggested Administrative Wording:</small>
              <p>"{result.suggested_wording}"</p>
              <button
                type="button"
                className="text-link-btn"
                onClick={() => onApplySuggestion(result.suggested_wording)}
              >
                Apply this suggested wording <ChevronRight size={13} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
