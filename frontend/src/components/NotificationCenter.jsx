import React from 'react';
import { Bell, Check, CheckCheck, X, AlertCircle, Info, ExternalLink } from 'lucide-react';

export default function NotificationCenter({ notifications, onMarkRead, onMarkAllRead, onClose, onNavigate }) {
  return (
    <div className="notif-dropdown">
      <div className="notif-header">
        <div className="flex-row items-center gap-2">
          <Bell size={16} className="text-teal" />
          <b>Notifications</b>
          <span className="notif-badge">{notifications.filter(n => !n.is_read).length} new</span>
        </div>
        <div className="flex-row items-center gap-2">
          <button className="text-link-btn" onClick={onMarkAllRead}>
            Mark all read
          </button>
          <button className="icon-btn" onClick={onClose}><X size={15} /></button>
        </div>
      </div>

      <div className="notif-list">
        {notifications.map(n => (
          <div key={n.id} className={`notif-item ${n.is_read ? 'read' : 'unread'}`}>
            <div className={`notif-icon-dot ${n.notification_type}`} />
            <div className="notif-body">
              <div className="notif-title-row">
                <b>{n.title}</b>
                <small>{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>
              </div>
              <p>{n.message}</p>
              <div className="notif-actions-row">
                {n.link_url && (
                  <button className="notif-action-btn" onClick={() => onNavigate(n.link_url)}>
                    View details <ExternalLink size={12} />
                  </button>
                )}
                {!n.is_read && (
                  <button className="icon-btn" onClick={() => onMarkRead(n.id)} title="Mark as read">
                    <Check size={14} />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
        {notifications.length === 0 && (
          <div className="p-6 text-center text-muted">
            <Bell size={24} className="mb-2 text-muted" />
            <p>No new notifications.</p>
          </div>
        )}
      </div>
    </div>
  );
}
