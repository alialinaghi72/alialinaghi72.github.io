def s(body): return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+body+'</svg>'
ICONS={
 'plan': s('<path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15M15 6v15"/>'),
 'target': s('<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/>'),
 'cube': s('<path d="M12 2.8l8 4.6v9.2l-8 4.6-8-4.6V7.4z"/><path d="M4 7.4l8 4.6 8-4.6M12 12v9.2"/>'),
 'db': s('<ellipse cx="11" cy="5.5" rx="7" ry="2.7"/><path d="M4 5.5v6c0 1.5 3.1 2.7 7 2.7M18 5.5v4M4 11.5v6c0 1.5 3.1 2.7 7 2.7"/><path d="M15 17.5l2 2 4-4.5"/>'),
 'audit': s('<path d="M14 3H6.5A1.5 1.5 0 005 4.5v15A1.5 1.5 0 006.5 21H11"/><path d="M14 3l4 4h-4zM8 9h6M8 12.5h4"/><circle cx="16.5" cy="16.5" r="3.2"/><path d="M19 19l2 2"/>'),
 'chart': s('<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/><path d="M15 6h4v4"/>'),
 'teach': s('<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c2 2 10 2 12 0v-5M22 9v6"/>'),
 'phone': s('<path d="M5 3h3.5l1.8 4.6-2.3 1.4a11 11 0 005.9 5.9l1.4-2.3L20 14.5V18a2 2 0 01-2 2A16 16 0 013 5a2 2 0 012-2z"/>'),
 'wa': s('<path d="M3.5 20.5l1.3-4.2A8.5 8.5 0 1112 20.5a8.4 8.4 0 01-4.3-1.2z"/><path d="M9 8.5c0 3.5 3 6.5 6.5 6.5l1-1.6-2-1-1 .9a4.6 4.6 0 01-2.3-2.3l.9-1-1-2z"/>'),
 'mail': s('<rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="M3.5 6l8.5 7 8.5-7"/>'),
 'in': s('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7.5 10v6.5M7.5 7.3v.2M11.5 16.5V10M11.5 13c0-2 1.2-3 2.7-3s2.3 1 2.3 3v3.5"/>'),
 'save': s('<path d="M12 3v12M7 10l5 5 5-5"/><path d="M4 17v2.5A1.5 1.5 0 005.5 21h13a1.5 1.5 0 001.5-1.5V17"/>'),
 'arrow': s('<path d="M5 12h14M13 6l6 6-6 6"/>'),
}
ICONS.update({
 'layers': s('<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 12.5l9 5 9-5M3 17l9 5 9-5"/>'),
 'wave': s('<path d="M2 12h3l2-6 3 12 3-9 2 6 2-3h5"/>'),
 'flask': s('<path d="M9 3h6M10 3v6L4.5 19a1.5 1.5 0 001.3 2h12.4a1.5 1.5 0 001.3-2L14 9V3"/><path d="M7 15h10"/>'),
 'satellite': s('<path d="M13 7l4 4-6 6-4-4z"/><path d="M15 5l2-2 4 4-2 2M9 15l-2 2-4-4 2-2"/><path d="M5 19a4 4 0 004-4"/>'),
 'gem': s('<path d="M6 3h12l3 6-9 12L3 9z"/><path d="M3 9h18M12 21L8.5 9 12 3l3.5 6z"/>'),
 'grid': s('<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>'),
})
