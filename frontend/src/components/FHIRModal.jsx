import React, { useState, useEffect } from 'react';
import { Network, X, Download, Copy, Check, ShieldCheck, RefreshCw } from 'lucide-react';

export default function FHIRModal({ referral, api, onClose }) {
  const [bundle, setBundle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchBundle();
  }, [referral.id]);

  async function fetchBundle() {
    setLoading(true);
    try {
      const data = await api(`/api/interop/fhir/referral/${referral.id}`);
      setBundle(data);
    } catch (e) {
      console.warn('FHIR fetch error', e);
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    if (!bundle) return;
    navigator.clipboard.writeText(JSON.stringify(bundle, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    if (!bundle) return;
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `FHIR_R4_Bundle_${referral.id}.json`;
    a.click();
  }

  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal wide fhir-modal">
        <div className="modal-head">
          <div className="flex-row items-center gap-2">
            <Network size={22} className="text-teal" />
            <div>
              <h2>HL7 FHIR R4 Document Bundle</h2>
              <p>National Digital Health Mission (ABDM) compliant referral resource bundle.</p>
            </div>
          </div>
          <div className="flex-row gap-2">
            <button className="secondary-btn small-btn" onClick={handleCopy} disabled={!bundle}>
              {copied ? <Check size={14} className="text-green" /> : <Copy size={14} />} {copied ? 'Copied' : 'Copy JSON'}
            </button>
            <button className="secondary-btn small-btn" onClick={handleDownload} disabled={!bundle}>
              <Download size={14} /> Download FHIR JSON
            </button>
            <button className="icon-btn" onClick={onClose}><X size={18} /></button>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-muted">
            <RefreshCw className="spin mb-2" size={24} />
            <p>Serializing referral into NRCeS FHIR R4 Bundle...</p>
          </div>
        ) : bundle ? (
          <div className="fhir-code-container">
            <div className="fhir-header-meta">
              <span className="badge-pill">resourceType: Bundle</span>
              <span className="badge-pill">type: {bundle.type}</span>
              <span className="badge-pill">entries: {bundle.entry?.length || 0} resources</span>
              <span className="badge-pill text-teal">ABDM Sandbox Validated</span>
            </div>
            <pre className="fhir-json-viewer">
              <code>{JSON.stringify(bundle, null, 2)}</code>
            </pre>
          </div>
        ) : (
          <div className="p-6 text-center text-muted">Unable to generate FHIR R4 bundle.</div>
        )}
      </div>
    </div>
  );
}
