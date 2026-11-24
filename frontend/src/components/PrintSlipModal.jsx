import React from 'react';
import { QRCodeCanvas } from 'qrcode.react';
import { Printer, Download, X, ShieldCheck, Building2, HeartPulse } from 'lucide-react';

export default function PrintSlipModal({ referral, onClose }) {
  function handlePrint() {
    window.print();
  }

  function handleDownloadQR() {
    const canvas = document.getElementById('printable-qr-canvas');
    if (!canvas) return;
    const url = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = url;
    a.download = `QR_${referral.id}.png`;
    a.click();
  }

  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal print-modal">
        <div className="modal-head no-print">
          <h2>Official Referral Slip & QR Slip</h2>
          <div className="flex-row gap-2">
            <button className="secondary-btn" onClick={handleDownloadQR}>
              <Download size={15} /> Download QR PNG
            </button>
            <button className="primary-btn" onClick={handlePrint}>
              <Printer size={15} /> Print Slip
            </button>
            <button className="icon-btn" onClick={onClose}><X size={18} /></button>
          </div>
        </div>

        {/* Printable Referral Slip */}
        <div className="referral-print-slip" id="referral-print-slip">
          <div className="slip-header">
            <div className="flex-row items-center gap-2">
              <HeartPulse size={26} className="text-teal" />
              <div>
                <h2>PRIMARY HEALTHCARE REFERRAL SLIP</h2>
                <small>Government Health Coordination Network · Ayushman Digital Protocol</small>
              </div>
            </div>
            <div className="slip-id-tag">
              <span>REFERRAL ID</span>
              <b>{referral.id}</b>
            </div>
          </div>

          <hr className="slip-divider" />

          <div className="slip-body-grid">
            <div className="slip-patient-info">
              <h3>Patient Identification</h3>
              <div className="info-row"><span>Full Name:</span><b>{referral.patient_name}</b></div>
              <div className="info-row"><span>Patient Code:</span><b>{referral.patient_code}</b></div>
              <div className="info-row"><span>Age / Sex:</span><b>{referral.age} Yrs / {referral.sex}</b></div>
              <div className="info-row"><span>Contact:</span><b>{referral.phone || 'Synthetic Registry Only'}</b></div>
              <div className="info-row"><span>Priority:</span><b className={`priority-tag ${referral.priority.toLowerCase()}`}>{referral.priority}</b></div>
            </div>

            <div className="slip-qr-box">
              <QRCodeCanvas
                id="printable-qr-canvas"
                value={referral.qr_token || JSON.stringify({ type: 'PHC_BRIDGE_REFERRAL', referralId: referral.id })}
                size={140}
                level="M"
              />
              <span className="qr-caption">Scan at hospital triage</span>
            </div>
          </div>

          <div className="slip-facility-box">
            <div className="facility-column">
              <small>Referring Facility (PHC)</small>
              <b>{referral.source_phc}</b>
              <span>Attending MO: {referral.referring_doctor_name || 'Medical Officer'}</span>
            </div>
            <div className="facility-arrow">➔</div>
            <div className="facility-column">
              <small>Receiving Destination</small>
              <b>{referral.destination}</b>
              <span>Specialist Triage Desk</span>
            </div>
          </div>

          <div className="slip-reason-box">
            <h4>Clinical Presentation / Rationale for Referral:</h4>
            <p>{referral.reason}</p>
          </div>

          <div className="slip-instructions-box">
            <h4>Instructions for Patient & Receiving Facility:</h4>
            <ol>
              <li>Present this digital slip or printed copy at the District Hospital referral registration counter.</li>
              <li>Receiving facility will scan the QR code to confirm patient handoff and synchronize status.</li>
              <li>Upon consultation completion, hospital outcome and back-referral notes will be returned to PHC.</li>
            </ol>
          </div>

          <div className="slip-footer">
            <div className="flex-row items-center gap-1 text-muted">
              <ShieldCheck size={14} />
              <span>Synthetic demonstration record. PHC Bridge Care Coordination Protocol.</span>
            </div>
            <span>Generated: {new Date(referral.created_at).toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
