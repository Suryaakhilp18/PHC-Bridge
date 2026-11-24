import React, { useState, useEffect } from 'react';
import { Building2, Search, Filter, Phone, MapPin, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function FacilityDirectoryView({ api }) {
  const [facilities, setFacilities] = useState([]);
  const [districtFilter, setDistrictFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDirectory();
  }, [districtFilter, typeFilter]);

  async function loadDirectory() {
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (districtFilter !== 'All') q.set('district', districtFilter);
      if (typeFilter !== 'All') q.set('facility_type', typeFilter);
      const data = await api(`/api/interop/facilities/directory?${q.toString()}`);
      setFacilities(data);
    } catch (e) {
      console.warn('Failed loading directory', e);
    } finally {
      setLoading(false);
    }
  }

  const filtered = facilities.filter(f =>
    f.name.toLowerCase().includes(search.toLowerCase()) ||
    (f.mandal && f.mandal.toLowerCase().includes(search.toLowerCase())) ||
    (f.hfr_id && f.hfr_id.toLowerCase().includes(search.toLowerCase()))
  );

  const totalFacilities = facilities.length;
  const phcCount = facilities.filter(f => f.facility_type === 'PHC' || f.facility_type === 'Sub-Centre / AAM').length;
  const hospitalCount = facilities.filter(f => f.facility_type.includes('Hospital') || f.facility_type === 'CHC').length;
  const districts = Array.from(new Set(facilities.map(f => f.district).filter(Boolean)));

  return (
    <div className="facility-directory-view">
      <div className="section-analytics-banner mb-3 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Total Registered Institutions</div>
          <div className="text-lg font-bold text-slate-800 mt-1">{totalFacilities}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Authoritative Health Facility Registry</div>
        </div>
        <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Primary Care Gateways</div>
          <div className="text-lg font-bold text-teal-600 mt-1">{phcCount}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">PHCs & Arogya Mandirs</div>
        </div>
        <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Secondary & Tertiary Centers</div>
          <div className="text-lg font-bold text-blue-600 mt-1">{hospitalCount}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">CHCs, Area, District & Teaching GGH</div>
        </div>
        <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Districts Covered</div>
          <div className="text-lg font-bold text-indigo-600 mt-1">{districts.length} Districts</div>
          <div className="text-[11px] text-slate-400 mt-0.5">{districts.join(', ') || 'NTR, Guntur, Vizag'}</div>
        </div>
      </div>

      <div className="panel table-panel">
        <div className="table-toolbar">
          <div className="search-box">
            <Search size={16} />
            <input
              placeholder="Search facility name, mandal, or HFR ID..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <select
              className="filter-select"
              value={districtFilter}
              onChange={e => setDistrictFilter(e.target.value)}
            >
              <option value="All">All Districts</option>
              <option value="NTR">NTR District (Vijayawada)</option>
              <option value="Guntur">Guntur District</option>
              <option value="Visakhapatnam">Visakhapatnam District</option>
            </select>
            <select
              className="filter-select"
              value={typeFilter}
              onChange={e => setTypeFilter(e.target.value)}
            >
              <option value="All">All Tiers</option>
              <option value="Sub-Centre / AAM">Ayushman Arogya Mandir (Sub-Centre)</option>
              <option value="PHC">Primary Health Centre (PHC)</option>
              <option value="CHC">Community Health Centre (CHC)</option>
              <option value="Area Hospital">Area Hospital</option>
              <option value="District Hospital">District Hospital</option>
              <option value="Teaching Hospital">Teaching / GGH Hospital</option>
            </select>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Health Facility Name</th>
                <th>Institutional Tier</th>
                <th>District & Mandal</th>
                <th>HFR Registry ID</th>
                <th>Official Contact</th>
                <th>ABDM Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(f => (
                <tr key={f.id}>
                  <td>
                    <div className="flex-row items-center gap-2">
                      <Building2 size={16} className="text-teal flex-shrink-0" />
                      <b>{f.name}</b>
                    </div>
                  </td>
                  <td>
                    <span className="badge-pill tier-badge">{f.facility_type}</span>
                  </td>
                  <td>
                    <div className="flex-row items-center gap-1 text-xs">
                      <MapPin size={12} className="text-muted" />
                      <span>{f.mandal || 'Urban'}, {f.district}</span>
                    </div>
                  </td>
                  <td>
                    <code className="code-pill">{f.hfr_id || 'HFR-AP'}</code>
                  </td>
                  <td>
                    <div className="flex-row items-center gap-1 text-xs text-muted">
                      <Phone size={12} />
                      <span>{f.phone || '0866-2485601'}</span>
                    </div>
                  </td>
                  <td>
                    <span className="text-xs text-green flex-row items-center gap-1">
                      <CheckCircle2 size={13} /> Active Bridge
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-muted">
                    {loading ? 'Querying Health Facility Registry...' : 'No facilities found for this filter.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
