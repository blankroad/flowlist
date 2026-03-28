/* ═══════════════════════════════════════
   FlowList — Client-side logic
   ═══════════════════════════════════════ */

// ── State ──
let currentView = 'inbox';
let currentEntityId = '';
let selectedTaskId = null;
let saveTimer = null;

const VIEW_CONFIG = {
  inbox:    { title: 'Inbox',    color: '#007aff', icon: 'inbox' },
  today:    { title: 'Today',    color: '#f5a623', icon: 'star' },
  upcoming: { title: 'Upcoming', color: '#ff3b30', icon: 'calendar' },
  anytime:  { title: 'Anytime',  color: '#8e8e93', icon: 'layers' },
  someday:  { title: 'Someday',  color: '#c7a46e', icon: 'cloud' },
  logbook:  { title: 'Logbook',  color: '#34c759', icon: 'check' },
};

const EMPTY_STATES = {
  inbox:    ['📥', 'Inbox is empty',          'Capture tasks here — process them later'],
  today:    ['⭐', 'Your day is clear',        'No tasks scheduled for today'],
  upcoming: ['📅', 'Nothing upcoming',         'Schedule tasks to see them here'],
  anytime:  ['📋', 'No open tasks',            'Tasks without a specific schedule appear here'],
  someday:  ['💭', 'Someday list is empty',    'Park ideas you might get to eventually'],
  logbook:  ['✅', 'No completed tasks yet',   'Completed tasks will appear here'],
  project:  ['📁', 'No tasks in this project', 'Add tasks to get started'],
  area:     ['🏷️', 'No tasks in this area',    'Assign tasks to this area'],
};

const SCHEDULE_COLORS = {
  inbox: '#007aff', today: '#f5a623', upcoming: '#ff3b30',
  anytime: '#8e8e93', someday: '#c7a46e',
};

// ── SVG Icons ──
const ICONS = {
  inbox: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="3" y="8" width="14" height="9" rx="2"/><path d="M3 12h4l1.5 2h3l1.5-2h4"/><path d="M10 3v6M7.5 6.5 10 9l2.5-2.5"/></svg>',
  star: '<svg viewBox="0 0 20 20" fill="currentColor" stroke="none"><path d="M10 2l2.35 4.76 5.25.77-3.8 3.7.9 5.24L10 14.27l-4.7 2.47.9-5.24-3.8-3.7 5.25-.77z"/></svg>',
  calendar: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="3" y="4" width="14" height="13" rx="2"/><path d="M3 8h14M7 2v3M13 2v3"/></svg>',
  layers: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M10 3 2 7l8 4 8-4z"/><path d="m2 11 8 4 8-4"/><path d="m2 15 8 4 8-4"/></svg>',
  cloud: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5.5 16A4 4 0 0 1 4 8.5a5 5 0 0 1 9.6-1.4A3.5 3.5 0 0 1 15.5 14H14"/><circle cx="8" cy="14" r="0.5" fill="currentColor"/><circle cx="11" cy="16" r="0.5" fill="currentColor"/></svg>',
  check: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="10" cy="10" r="7"/><path d="m7 10 2 2.5 4-4.5"/></svg>',
  folder: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M3 6V5a1 1 0 0 1 1-1h4l2 2h6a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6z"/></svg>',
  tag: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M3 3h6.5l7.2 7.2a1 1 0 0 1 0 1.4l-5.1 5.1a1 1 0 0 1-1.4 0L3 9.5V3z"/><circle cx="7" cy="7" r="1" fill="currentColor"/></svg>',
};

// ── API Helpers ──
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  return res.json();
}

// ── Sidebar ──
function renderSidebar(data) {
  const nav = document.getElementById('gtd-nav');
  nav.innerHTML = '';

  for (const [key, cfg] of Object.entries(VIEW_CONFIG)) {
    const count = data.counts[key] || 0;
    const item = document.createElement('div');
    item.className = `nav-item${currentView === key ? ' active' : ''}`;
    item.onclick = () => navigate(key);
    item.innerHTML = `
      <div class="nav-icon" style="color:${cfg.color}">${ICONS[cfg.icon]}</div>
      <div class="nav-label">${cfg.title}</div>
      ${count > 0 ? `<div class="nav-count">${count}</div>` : ''}
    `;
    nav.appendChild(item);
  }

  // Projects
  const projList = document.getElementById('projects-list');
  projList.innerHTML = '';
  for (const p of data.projects) {
    const item = document.createElement('div');
    item.className = `nav-item${currentView === 'project' && currentEntityId === p.id ? ' active' : ''}`;
    item.onclick = () => navigate('project', p.id);
    item.innerHTML = `
      <div class="nav-icon" style="color:#8e8e93">${ICONS.folder}</div>
      <div class="nav-label">${esc(p.title)}</div>
      ${p.task_count > 0 ? `<div class="nav-count">${p.task_count}</div>` : ''}
    `;
    projList.appendChild(item);
  }

  // Areas
  const areaList = document.getElementById('areas-list');
  areaList.innerHTML = '';
  for (const a of data.areas) {
    const item = document.createElement('div');
    item.className = `nav-item${currentView === 'area' && currentEntityId === a.id ? ' active' : ''}`;
    item.onclick = () => navigate('area', a.id);
    item.innerHTML = `
      <div class="nav-icon" style="color:#af7ac5">${ICONS.tag}</div>
      <div class="nav-label">${esc(a.title)}</div>
    `;
    areaList.appendChild(item);
  }
}

// ── Navigation ──
async function navigate(view, entityId = '') {
  currentView = view;
  currentEntityId = entityId;
  selectedTaskId = null;
  closeDetail();
  await loadTasks();
  await loadSidebar();
}

async function loadSidebar() {
  const data = await api('/api/sidebar');
  renderSidebar(data);
}

async function loadTasks() {
  const params = currentEntityId ? `?entity_id=${currentEntityId}` : '';
  const data = await api(`/api/tasks/view/${currentView}${params}`);

  document.getElementById('view-title').textContent = data.title;

  const countEl = document.getElementById('view-count');
  const total = data.tasks.length;
  if (total > 0) {
    countEl.textContent = total;
    countEl.classList.remove('hidden');
  } else {
    countEl.classList.add('hidden');
  }

  const listEl = document.getElementById('task-list');
  const emptyEl = document.getElementById('empty-state');

  if (total === 0) {
    listEl.innerHTML = '';
    const es = EMPTY_STATES[currentView] || EMPTY_STATES.inbox;
    emptyEl.querySelector('.empty-icon').textContent = es[0];
    emptyEl.querySelector('.empty-title').textContent = es[1];
    emptyEl.querySelector('.empty-subtitle').textContent = es[2];
    emptyEl.classList.remove('hidden');
    listEl.style.display = 'none';
    return;
  }

  emptyEl.classList.add('hidden');
  listEl.style.display = '';
  listEl.innerHTML = '';

  if (data.groups && data.groups.length > 0) {
    for (const group of data.groups) {
      const header = document.createElement('div');
      header.className = 'section-title';
      header.textContent = group.name;
      listEl.appendChild(header);
      for (const task of group.tasks) {
        listEl.appendChild(createTaskItem(task));
      }
    }
  } else {
    for (const task of data.tasks) {
      listEl.appendChild(createTaskItem(task));
    }
  }
}

// ── Task Item ──
function createTaskItem(task) {
  const el = document.createElement('div');
  el.className = `task-item${task.status === 'completed' ? ' completed' : ''}${selectedTaskId === task.id ? ' selected' : ''}`;
  el.onclick = (e) => {
    if (e.target.closest('.checkbox')) return;
    selectTask(task.id);
  };

  const isCompleted = task.status === 'completed';

  let metaHtml = '';
  if (!isCompleted) {
    const badges = [];
    if (task.due_date) badges.push(dueDateBadge(task.due_date));
    if (task.tags) {
      for (const t of task.tags.slice(0, 3)) {
        const bg = hexToRgba(t.color || '#007aff', 0.12);
        badges.push(`<span class="tag-pill" style="background:${bg};color:${t.color || '#007aff'}">${esc(t.title)}</span>`);
      }
    }
    if (badges.length) metaHtml = `<div class="task-meta">${badges.join('')}</div>`;
  }

  let notesHtml = '';
  if (task.notes && !isCompleted) {
    const first = task.notes.split('\n')[0].substring(0, 80);
    if (first.trim()) notesHtml = `<div class="task-notes-preview">${esc(first)}</div>`;
  }

  el.innerHTML = `
    <div class="checkbox${isCompleted ? ' checked' : ''}" onclick="toggleTask('${task.id}', ${!isCompleted})"></div>
    <div class="task-content">
      <div class="task-title">${esc(task.title)}</div>
      ${notesHtml}
      ${metaHtml}
    </div>
  `;

  return el;
}

function dueDateBadge(dateStr) {
  const today = new Date(); today.setHours(0,0,0,0);
  const due = new Date(dateStr + 'T00:00:00');
  const diff = Math.floor((due - today) / 86400000);

  let text, cls;
  if (diff < 0) { text = 'Overdue'; cls = 'badge-overdue'; }
  else if (diff === 0) { text = 'Today'; cls = 'badge-today'; }
  else if (diff === 1) { text = 'Tomorrow'; cls = 'badge-tomorrow'; }
  else if (diff < 7) { text = due.toLocaleDateString('en', { weekday: 'long' }); cls = 'badge-default'; }
  else { text = due.toLocaleDateString('en', { month: 'short', day: 'numeric' }); cls = 'badge-default'; }

  return `<span class="badge ${cls}">📅 ${text}</span>`;
}

// ── Task Actions ──
async function toggleTask(taskId, complete) {
  const action = complete ? 'complete' : 'uncomplete';
  await api(`/api/tasks/${taskId}/${action}`, { method: 'POST' });
  setTimeout(async () => {
    await loadTasks();
    await loadSidebar();
  }, complete ? 400 : 0);
}

async function selectTask(taskId) {
  selectedTaskId = taskId;
  // Highlight in list
  document.querySelectorAll('.task-item').forEach(el => el.classList.remove('selected'));
  event?.target?.closest('.task-item')?.classList.add('selected');

  const task = await api(`/api/tasks/${taskId}`);
  showDetail(task);
}

// ── Detail Panel ──
function showDetail(task) {
  const panel = document.getElementById('detail-panel');
  panel.classList.remove('hidden');

  // Schedule badge
  const badge = document.getElementById('detail-schedule-badge');
  const color = SCHEDULE_COLORS[task.schedule] || '#8e8e93';
  badge.textContent = task.schedule.charAt(0).toUpperCase() + task.schedule.slice(1);
  badge.style.background = hexToRgba(color, 0.12);
  badge.style.color = color;

  document.getElementById('detail-title').value = task.title;
  document.getElementById('detail-notes').value = task.notes || '';
  document.getElementById('detail-schedule').value = task.schedule;
  document.getElementById('detail-due-date').value = task.due_date || '';

  // Checklist
  renderChecklist(task.checklist_items || []);

  // Attach save listeners
  const saveFields = ['detail-title', 'detail-notes', 'detail-schedule', 'detail-due-date'];
  for (const id of saveFields) {
    const el = document.getElementById(id);
    el.oninput = () => scheduleSave(task.id);
    el.onchange = () => scheduleSave(task.id);
  }

  // Store current task id
  panel.dataset.taskId = task.id;
}

function closeDetail() {
  document.getElementById('detail-panel').classList.add('hidden');
  selectedTaskId = null;
  document.querySelectorAll('.task-item').forEach(el => el.classList.remove('selected'));
}

function scheduleSave(taskId) {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => saveTask(taskId), 500);
}

async function saveTask(taskId) {
  await api(`/api/tasks/${taskId}`, {
    method: 'PUT',
    body: {
      title: document.getElementById('detail-title').value,
      notes: document.getElementById('detail-notes').value,
      schedule: document.getElementById('detail-schedule').value,
      due_date: document.getElementById('detail-due-date').value || null,
    },
  });
  await loadTasks();
  await loadSidebar();
}

async function deleteCurrentTask() {
  const panel = document.getElementById('detail-panel');
  const taskId = panel.dataset.taskId;
  if (!taskId || !confirm('Delete this task?')) return;
  await api(`/api/tasks/${taskId}`, { method: 'DELETE' });
  closeDetail();
  await loadTasks();
  await loadSidebar();
}

// ── Checklist ──
function renderChecklist(items) {
  const container = document.getElementById('checklist-items');
  container.innerHTML = '';

  const done = items.filter(i => i.is_done).length;
  const progress = document.getElementById('checklist-progress');
  progress.textContent = items.length > 0 ? `${done}/${items.length}` : '';

  for (const item of items) {
    const el = document.createElement('div');
    el.className = 'checklist-item';
    el.innerHTML = `
      <div class="cl-checkbox${item.is_done ? ' checked' : ''}"
           onclick="toggleChecklistItem('${item.id}', ${!item.is_done})"></div>
      <input class="cl-title${item.is_done ? ' done' : ''}" value="${esc(item.title)}"
             onchange="updateChecklistTitle('${item.id}', this.value)">
      <button class="cl-delete" onclick="deleteChecklistItem('${item.id}')">&times;</button>
    `;
    container.appendChild(el);
  }
}

async function addChecklistItem() {
  const panel = document.getElementById('detail-panel');
  const taskId = panel.dataset.taskId;
  if (!taskId) return;
  await api(`/api/tasks/${taskId}/checklist`, { method: 'POST', body: { title: 'New item' } });
  const task = await api(`/api/tasks/${taskId}`);
  renderChecklist(task.checklist_items || []);
}

async function toggleChecklistItem(itemId, isDone) {
  await api(`/api/checklist/${itemId}`, { method: 'PUT', body: { is_done: isDone } });
  const panel = document.getElementById('detail-panel');
  const task = await api(`/api/tasks/${panel.dataset.taskId}`);
  renderChecklist(task.checklist_items || []);
}

async function updateChecklistTitle(itemId, title) {
  await api(`/api/checklist/${itemId}`, { method: 'PUT', body: { title } });
}

async function deleteChecklistItem(itemId) {
  await api(`/api/checklist/${itemId}`, { method: 'DELETE' });
  const panel = document.getElementById('detail-panel');
  const task = await api(`/api/tasks/${panel.dataset.taskId}`);
  renderChecklist(task.checklist_items || []);
}

// ── New Task ──
document.getElementById('new-task-input').addEventListener('keydown', async (e) => {
  if (e.key === 'Enter') {
    const input = e.target;
    const title = input.value.trim();
    if (!title) return;

    const body = { title };
    if (['today', 'upcoming', 'anytime', 'someday'].includes(currentView)) {
      body.schedule = currentView;
    } else if (currentView === 'project') {
      body.project_id = currentEntityId;
      body.schedule = 'anytime';
    } else if (currentView === 'area') {
      body.area_id = currentEntityId;
      body.schedule = 'anytime';
    }

    await api('/api/tasks', { method: 'POST', body });
    input.value = '';
    await loadTasks();
    await loadSidebar();
  }
});

// ── Search ──
let searchTimer = null;
const searchOverlay = document.getElementById('search-overlay');
const searchInput = document.getElementById('search-input');

searchInput.addEventListener('input', () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(doSearch, 200);
});

async function doSearch() {
  const q = searchInput.value.trim();
  const resultsEl = document.getElementById('search-results');
  if (!q) { resultsEl.innerHTML = ''; return; }

  const tasks = await api(`/api/search?q=${encodeURIComponent(q)}`);
  if (tasks.length === 0) {
    resultsEl.innerHTML = '<div class="search-no-results">No results found</div>';
    return;
  }

  resultsEl.innerHTML = '';
  for (const t of tasks) {
    const el = document.createElement('div');
    el.className = 'search-result-item';
    el.onclick = () => {
      closeSearch();
      navigate(t.status === 'completed' ? 'logbook' : t.schedule).then(() => selectTask(t.id));
    };
    const dotColor = t.status === 'completed' ? '#34c759' : '#007aff';
    const meta = t.schedule.charAt(0).toUpperCase() + t.schedule.slice(1);
    el.innerHTML = `
      <div class="result-dot" style="background:${dotColor}"></div>
      <div>
        <div class="result-title">${esc(t.title)}</div>
        <div class="result-meta">${meta}${t.notes ? ' · ' + esc(t.notes.split('\n')[0].substring(0, 50)) : ''}</div>
      </div>
    `;
    resultsEl.appendChild(el);
  }
}

function openSearch() {
  searchOverlay.classList.remove('hidden');
  searchInput.focus();
  searchInput.select();
}

function closeSearch() {
  searchOverlay.classList.add('hidden');
  searchInput.value = '';
  document.getElementById('search-results').innerHTML = '';
}

// ── Quick Entry ──
const QE_SCHEDULES = [
  { key: 'inbox', label: 'Inbox', color: '#007aff' },
  { key: 'today', label: 'Today', color: '#f5a623' },
  { key: 'upcoming', label: 'Upcoming', color: '#ff3b30' },
  { key: 'anytime', label: 'Anytime', color: '#8e8e93' },
  { key: 'someday', label: 'Someday', color: '#c7a46e' },
];

let qeSchedule = 'inbox';

function initQuickEntry() {
  const pills = document.getElementById('qe-pills');
  pills.innerHTML = '';
  for (const s of QE_SCHEDULES) {
    const btn = document.createElement('button');
    btn.className = `qe-pill${s.key === qeSchedule ? ' active' : ''}`;
    btn.textContent = s.label;
    btn.style.cssText = s.key === qeSchedule
      ? `background:${s.color};border-color:${s.color};color:#fff;`
      : '';
    btn.onclick = () => {
      qeSchedule = s.key;
      initQuickEntry();
    };
    pills.appendChild(btn);
  }
}

function openQuickEntry() {
  qeSchedule = 'inbox';
  document.getElementById('qe-title').value = '';
  initQuickEntry();
  document.getElementById('quick-entry-backdrop').classList.remove('hidden');
  setTimeout(() => document.getElementById('qe-title').focus(), 50);
}

function closeQuickEntry() {
  document.getElementById('quick-entry-backdrop').classList.add('hidden');
}

async function submitQuickEntry() {
  const title = document.getElementById('qe-title').value.trim();
  if (!title) return;
  await api('/api/tasks', { method: 'POST', body: { title, schedule: qeSchedule } });
  closeQuickEntry();
  await loadTasks();
  await loadSidebar();
}

document.getElementById('qe-title').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') submitQuickEntry();
  if (e.key === 'Escape') closeQuickEntry();
});

// ── Project / Area creation ──
async function promptCreate(type) {
  const label = type === 'project' ? 'Project' : 'Area';
  const title = prompt(`New ${label} name:`);
  if (!title?.trim()) return;
  await api(`/api/${type}s`, { method: 'POST', body: { title: title.trim() } });
  await loadSidebar();
}

// ── Keyboard Shortcuts ──
document.addEventListener('keydown', (e) => {
  const meta = e.metaKey || e.ctrlKey;

  // Cmd+F: Search
  if (meta && e.key === 'f') {
    e.preventDefault();
    if (searchOverlay.classList.contains('hidden')) openSearch();
    else closeSearch();
    return;
  }

  // Cmd+Shift+N: Quick Entry
  if (meta && e.shiftKey && e.key === 'N') {
    e.preventDefault();
    openQuickEntry();
    return;
  }

  // Cmd+N: Focus new task input
  if (meta && !e.shiftKey && e.key === 'n') {
    e.preventDefault();
    document.getElementById('new-task-input').focus();
    return;
  }

  // Escape
  if (e.key === 'Escape') {
    if (!searchOverlay.classList.contains('hidden')) { closeSearch(); return; }
    if (!document.getElementById('quick-entry-backdrop').classList.contains('hidden')) { closeQuickEntry(); return; }
    if (!document.getElementById('detail-panel').classList.contains('hidden')) { closeDetail(); return; }
  }

  // Cmd+1-6: Switch views
  if (meta && e.key >= '1' && e.key <= '6') {
    e.preventDefault();
    const views = ['inbox', 'today', 'upcoming', 'anytime', 'someday', 'logbook'];
    const idx = parseInt(e.key) - 1;
    if (idx < views.length) navigate(views[idx]);
  }
});

// ── Helpers ──
function esc(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ── Init ──
(async () => {
  await loadSidebar();
  await loadTasks();
})();
