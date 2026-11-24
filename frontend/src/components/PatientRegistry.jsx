import React, { useState, useEffect } from 'react';
import { Users, Search, Plus, UserPlus, Phone, Calendar, Building2, ClipboardList, ArrowUpRight } from 'lucide-react';

export default function PatientRegistry({ api, onOpenReferral, onCreateReferralForPatient }) {
  const [patients, setPatients] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [newPatient, setNewPatient] = useState({
    full_name: '',
    age: '',
    sex: 'Female',
    phone: '',
    address: ''
  });

  useEffect(() => {
    loadPatients();
  }, []);

  async function loadPatients(q = '') {
    setLoading(true);
    try {
      const data = await api(`/api/patients${q ? `?query=${encodeURIComponent(q)}` : ''}`);
      setPatients(data);
    } catch (e) {
      console.warn('Failed loading patients', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    try {
      await api('/api/patients', {
        method: 'POST',
        body: JSON.stringify({
          ...newPatient,
          age: parseInt(newPatient.age)
        })
      });
      setShowRegister(false);
      setNewPatient({ full_name: '', age: '', sex: 'Female', phone: '', address: '' });
      loadPatients();
    } catch (err) {
      alert(err.message || 'Error registering patient');
    }
  }

  return (
    <div className="patients-view">
      <div className="panel table-panel">
        <div className="table-toolbar flex-between">
          <div className="search-box">
            <Search size={16} />
            <input
              placeholder="Search patients by name, code (SYN-1001), phone..."
              value={query}
              onChange={e => {
                setQuery(e.target.value);
                loadPatients(e.target.value);
              }}
            />
          </div>
          <button className="primary-btn" onClick={() => setShowRegister(true)}>
            <UserPlus size={16} /> Register Patient
          </button>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Patient Name & Code</th>
                <th>Demographics</th>
                <th>Registered PHC</th>
                <th>Contact</th>
                <th>Referrals</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map(p => (
                <tr key={p.id}>
                  <td>
                    <div className="patient-name-cell">
                      <b>{p.full_name}</b>
                      <span className="code-pill">{p.patient_code}</span>
                    </div>
                  </td>
                  <td>{p.age} yrs · {p.sex}</td>
                  <td>
                    <span className="facility-cell">
                      <Building2 size={13} className="text-teal" />
                      {p.registered_phc_name || 'Primary Centre'}
                    </span>
                  </td>
                  <td>{p.phone || '—'}</td>
                  <td>
                    <span className="count-pill">{p.referral_count} recorded</span>
                  </td>
                  <td>
                    <button
                      className="secondary-btn small-btn"
                      onClick={() => onCreateReferralForPatient(p)}
                    >
                      <Plus size={13} /> New Referral
                    </button>
                  </td>
                </tr>
              ))}
              {patients.length === 0 && (
                <tr>
                  <td colSpan="6" className="text-center p-6 text-muted">
                    {loading ? 'Loading patient registry...' : 'No registered patients found.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showRegister && (
        <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && setShowRegister(false)}>
          <div className="modal">
            <div className="modal-head">
              <h2>Register Synthetic Patient</h2>
              <p>Add a new patient profile to the healthcare coordination registry.</p>
            </div>
            <form onSubmit={handleRegister} className="form-grid">
              <label className="full">
                Full Name
                <input
                  required
                  value={newPatient.full_name}
                  onChange={e => setNewPatient({ ...newPatient, full_name: e.target.value })}
                  placeholder="e.g. Ramesh Kumar"
                />
              </label>
              <label>
                Age
                <input
                  required
                  type="number"
                  min="0"
                  max="120"
                  value={newPatient.age}
                  onChange={e => setNewPatient({ ...newPatient, age: e.target.value })}
                />
              </label>
              <label>
                Sex
                <select
                  value={newPatient.sex}
                  onChange={e => setNewPatient({ ...newPatient, sex: e.target.value })}
                >
                  <option>Female</option>
                  <option>Male</option>
                  <option>Other</option>
                </select>
              </label>
              <label className="full">
                Phone Number (Synthetic)
                <input
                  value={newPatient.phone}
                  onChange={e => setNewPatient({ ...newPatient, phone: e.target.value })}
                  placeholder="9876543210"
                />
              </label>
              <label className="full">
                Residential Village / Ward
                <input
                  value={newPatient.address}
                  onChange={e => setNewPatient({ ...newPatient, address: e.target.value })}
                  placeholder="e.g. Ward 3, Lakshmi Nagar"
                />
              </label>
              <div className="full modal-actions">
                <button type="button" className="secondary-btn" onClick={() => setShowRegister(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-btn">
                  Register
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
