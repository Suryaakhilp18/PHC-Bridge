import React, { useState, useEffect, useRef } from 'react';
import { Camera, X, CheckCircle2, AlertCircle, RefreshCw, QrCode } from 'lucide-react';

export default function QRScannerModal({ onClose, onScanSuccess }) {
  const [hasCamera, setHasCamera] = useState(true);
  const [cameraActive, setCameraActive] = useState(false);
  const [error, setError] = useState('');
  const [manualCode, setManualCode] = useState('');
  const [scanning, setScanning] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  async function startCamera() {
    setError('');
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setHasCamera(false);
        setError('Camera API is not supported on this device/browser.');
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setCameraActive(true);
      }
    } catch (err) {
      console.warn('Camera access denied or unavailable:', err);
      setHasCamera(false);
      setError('Camera access not granted or device has no camera. Use manual referral ID input below.');
    }
  }

  function stopCamera() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  }

  async function handleManualSubmit(e) {
    e.preventDefault();
    if (!manualCode.trim()) return;
    setScanning(true);
    try {
      await onScanSuccess(manualCode.trim());
      onClose();
    } catch (err) {
      setError(err.message || 'Invalid referral code or signature');
    } finally {
      setScanning(false);
    }
  }

  function simulateScan(code) {
    setScanning(true);
    setTimeout(async () => {
      try {
        await onScanSuccess(code);
        onClose();
      } catch (err) {
        setError(err.message || 'Scanned referral not found');
      } finally {
        setScanning(false);
      }
    }, 400);
  }

  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-head">
          <div className="flex-row items-center gap-2">
            <QrCode className="text-teal" size={22} />
            <div>
              <h2>Scan Referral QR Code</h2>
              <p>Scan the digital patient slip or enter the referral ID manually.</p>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="scanner-container">
          {hasCamera && cameraActive ? (
            <div className="video-viewport">
              <video ref={videoRef} playsInline muted className="camera-video" />
              <div className="scanner-target-reticle">
                <span className="reticle-line" />
              </div>
              <small className="scanner-overlay-hint">Position the QR code within the frame</small>
            </div>
          ) : (
            <div className="scanner-fallback-box">
              <QrCode size={48} className="text-muted" />
              <b>Optical Scanner Ready</b>
              <p>{error || 'Camera preview not available. Enter referral ID or use quick sample codes below.'}</p>
            </div>
          )}

          <div className="quick-test-chips">
            <span className="text-xs text-muted">Quick test samples:</span>
            <button type="button" className="chip-btn" onClick={() => simulateScan('PHC-2026-00124')}>
              PHC-2026-00124 (Urgent)
            </button>
            <button type="button" className="chip-btn" onClick={() => simulateScan('PHC-2026-00123')}>
              PHC-2026-00123 (Routine)
            </button>
          </div>

          <form onSubmit={handleManualSubmit} className="manual-scan-form">
            <div className="search-box full">
              <input
                type="text"
                value={manualCode}
                onChange={e => setManualCode(e.target.value)}
                placeholder="Enter Referral ID (e.g. PHC-2026-00124)"
                autoFocus
              />
              <button type="submit" className="primary-btn" disabled={scanning || !manualCode.trim()}>
                {scanning ? <RefreshCw className="spin" size={16} /> : 'Lookup'}
              </button>
            </div>
          </form>

          {error && (
            <div className="banner-alert error">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
