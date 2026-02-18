// ─── State ────────────────────────────────────────────────────────────────────

let currentRunId   = null;
let pollingInterval = null;
const logs = [];

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('blogForm').addEventListener('submit', handleFormSubmit);
    document.getElementById('downloadBtn').addEventListener('click', downloadMarkdown);

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    loadPastBlogs();
});

// ─── Form submission ──────────────────────────────────────────────────────────

async function handleFormSubmit(e) {
    e.preventDefault();

    const topic          = document.getElementById('topic').value.trim();
    const modelProvider  = document.getElementById('modelProvider').value;
    const imagesEnabled  = document.getElementById('imagesEnabled').checked;

    if (!topic) {
        showToast('Please enter a topic', 'error');
        return;
    }

    if (!modelProvider) {
        showToast('Please select a model provider', 'error');
        return;
    }

    const btn = document.getElementById('generateBtn');
    btn.disabled    = true;
    btn.textContent = 'Generating…';

    // Reset live log box for this new run
    resetLiveLog();

    try {
        const response = await fetch('/api/v1/blog/generate', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ 
                topic, 
                images_enabled: imagesEnabled,
                provider: modelProvider 
            })
        });

        if (!response.ok) throw new Error('Failed to start generation');

        const data  = await response.json();
        currentRunId = data.run_id;

        showScreen('loading');
        startPolling();

    } catch (error) {
        showToast('Error: ' + error.message, 'error');
        btn.disabled    = false;
        btn.textContent = 'Generate Blog';
    }
}

// ─── Polling ──────────────────────────────────────────────────────────────────

function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);

    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/v1/blog/status/${currentRunId}`);
            if (!response.ok) throw new Error('Failed to get status');

            const data = await response.json();

            // ── Update loading message ────────────────────────────────────────
            if (data.message) {
                document.getElementById('loadingMessage').textContent = data.message;
            }

            // ── Feed live logs ────────────────────────────────────────────────
            if (data.logs && Array.isArray(data.logs) && data.logs.length > 0) {
                updateLiveLog(data.logs);

                // Keep master logs array in sync for the Logs tab
                logs.length = 0;
                logs.push(...data.logs);
            }

            // ── Done / failed ─────────────────────────────────────────────────
            if (data.status === 'completed') {
                stopPolling();
                hideLiveLogPulse();   // stop the blinking dot
                await showResults(data);
                loadPastBlogs();
                resetGenerateButton();

            } else if (data.status === 'failed') {
                stopPolling();
                hideLiveLogPulse();
                showToast('Generation failed: ' + data.message, 'error');
                showScreen('welcome');
                resetGenerateButton();
            }

        } catch (error) {
            addLog('Error checking status: ' + error.message);
        }
    }, 2000);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

function resetGenerateButton() {
    const btn       = document.getElementById('generateBtn');
    btn.disabled    = false;
    btn.textContent = 'Generate Blog';
}

// ─── Live Log Box ─────────────────────────────────────────────────────────────

let lastLogCount = 0;

function resetLiveLog() {
    lastLogCount = 0;
    document.getElementById('liveLogContent').innerHTML = '';
    document.getElementById('liveLogBox').classList.remove('visible');
}

function updateLiveLog(serverLogs) {
    if (!serverLogs || serverLogs.length === 0) return;

    const box     = document.getElementById('liveLogBox');
    const content = document.getElementById('liveLogContent');

    // Show the box as soon as first log arrives
    if (!box.classList.contains('visible')) {
        box.classList.add('visible');
    }

    // Only append lines we haven't seen yet
    const newLines = serverLogs.slice(lastLogCount);
    lastLogCount   = serverLogs.length;

    newLines.forEach(line => {
        const span = document.createElement('span');
        span.className = 'log-line ' + classifyLogLine(line);
        span.textContent = line;
        content.appendChild(span);
        content.appendChild(document.createTextNode('\n'));
    });

    // Auto-scroll to bottom
    content.scrollTop = content.scrollHeight;
}

function classifyLogLine(line) {
    const lower = line.toLowerCase();
    if (lower.includes('error') || lower.includes('failed')) return 'error';
    if (lower.includes('warn'))                               return 'warn';
    if (lower.includes('done') || lower.includes('complet') || lower.includes('success')) return 'done';
    return 'info';
}

function hideLiveLogPulse() {
    const dot = document.querySelector('.log-dot');
    if (dot) {
        dot.style.animation = 'none';
        dot.style.background = '#8e8e93';
    }
}

// ─── Results ──────────────────────────────────────────────────────────────────

async function showResults(data) {
    showScreen('results');

    if (data.plan) renderPlan(data.plan);
    await renderPreview(data);
    renderImages(data);

    // Populate the Logs tab from our stored logs array
    document.getElementById('logsContent').value = logs.join('\n');
}

function renderPlan(plan) {
    let html = `
        <div class="plan-meta">
            <div class="plan-meta-item">
                <div class="plan-meta-label">Title</div>
                <div class="plan-meta-value">${escapeHtml(plan.blog_title)}</div>
            </div>
            <div class="plan-meta-item">
                <div class="plan-meta-label">Audience</div>
                <div class="plan-meta-value">${escapeHtml(plan.audience)}</div>
            </div>
            <div class="plan-meta-item">
                <div class="plan-meta-label">Tone</div>
                <div class="plan-meta-value">${escapeHtml(plan.tone)}</div>
            </div>
            <div class="plan-meta-item">
                <div class="plan-meta-label">Blog Kind</div>
                <div class="plan-meta-value">${escapeHtml(plan.blog_kind)}</div>
            </div>
        </div>
    `;

    if (plan.tasks && plan.tasks.length > 0) {
        html += '<h3 style="font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--text-tertiary);margin-bottom:10px;">Tasks</h3>';
        html += '<table class="tasks-table"><thead><tr>';
        html += '<th>ID</th><th>Title</th><th>Words</th><th>Features</th>';
        html += '</tr></thead><tbody>';

        plan.tasks.forEach(task => {
            const badges = [];
            if (task.requires_research)  badges.push('<span class="task-badge">Research</span>');
            if (task.requires_citations) badges.push('<span class="task-badge">Citations</span>');
            if (task.requires_code)      badges.push('<span class="task-badge">Code</span>');

            html += `
                <tr>
                    <td>${task.id}</td>
                    <td>${escapeHtml(task.title)}</td>
                    <td>${task.target_words}</td>
                    <td>${badges.join('') || '—'}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
    }

    document.getElementById('planContent').innerHTML = html;
}

async function renderPreview(data) {
    const previewContent = document.getElementById('previewContent');

    if (!currentRunId) {
        previewContent.innerHTML = '<p style="color:var(--text-tertiary)">No blog generated yet.</p>';
        return;
    }

    try {
        const response = await fetch(`/api/v1/blog/content/${currentRunId}`);
        if (!response.ok) {
            previewContent.innerHTML = '<p style="color:var(--error)">Failed to load blog content.</p>';
            return;
        }

        const contentData = await response.json();
        let markdown = contentData.content;
        
        // Replace image paths with API URLs
        markdown = markdown.replace(
            /!\[([^\]]*)\]\((?:\.\.\/)?images\/([^)]+)\)/g, 
            `![$1](/api/v1/blog/images/${currentRunId}/$2)`
        );

        let html = markdown
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim,  '<h2>$1</h2>')
            .replace(/^# (.*$)/gim,   '<h1>$1</h1>')
            .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
            .replace(/\*\*(.+?)\*\*/g,     '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g,         '<em>$1</em>')
            .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%;height:auto;border-radius:6px;margin:16px 0;">')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g,        '<code>$1</code>')
            .split('\n\n')
            .map(para => {
                if (para.startsWith('<') || !para.trim()) return para;
                return `<p>${para.replace(/\n/g, '<br>')}</p>`;
            })
            .join('\n');

        previewContent.innerHTML = html;

    } catch (error) {
        previewContent.innerHTML = '<p style="color:var(--error)">Error loading blog content.</p>';
        addLog('Error fetching markdown: ' + error.message);
    }
}

function renderImages(data) {
    const html = (data.images_count && data.images_count > 0)
        ? `<p>${data.images_count} image(s) generated and saved with your blog.</p>`
        : '<p style="color:var(--text-tertiary)">No images were generated for this blog.</p>';
    document.getElementById('imagesContent').innerHTML = html;
}

// ─── Past Blogs ───────────────────────────────────────────────────────────────

async function loadPastBlogs() {
    try {
        const response = await fetch('/api/v1/blog/list');
        if (!response.ok) throw new Error('Failed to load blogs');

        const data  = await response.json();
        const listEl = document.getElementById('pastBlogsList');

        if (!data.blogs || data.blogs.length === 0) {
            listEl.innerHTML = '<p style="color:var(--text-tertiary);font-size:13px;">No past blogs yet.</p>';
            return;
        }

        const blogs = data.blogs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        listEl.innerHTML = blogs.map(blog => `
            <div class="blog-item" onclick="loadBlog('${blog.run_id}')">
                <div class="blog-item-title">${escapeHtml(blog.topic || 'Untitled')}</div>
                <div class="blog-item-meta">
                    <span class="status-badge status-${blog.status}">${blog.status}</span>
                    ${new Date(blog.created_at).toLocaleDateString()}
                </div>
            </div>
        `).join('');

    } catch (_) {
        document.getElementById('pastBlogsList').innerHTML =
            '<p style="color:var(--error);font-size:13px;">Error loading blogs.</p>';
    }
}

async function loadBlog(runId) {
    try {
        const response = await fetch(`/api/v1/blog/status/${runId}`);
        if (!response.ok) throw new Error('Failed to load blog');

        const data = await response.json();
        if (data.status !== 'completed') {
            showToast('This blog is not yet completed', 'error');
            return;
        }

        currentRunId = runId;

        // Populate logs from stored data
        if (data.logs && Array.isArray(data.logs)) {
            logs.length = 0;
            logs.push(...data.logs);
        }

        showResults(data);

    } catch (_) {
        showToast('Failed to load blog', 'error');
    }
}

// ─── Download ─────────────────────────────────────────────────────────────────

async function downloadMarkdown() {
    if (!currentRunId) {
        showToast('No blog to download', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/v1/blog/download/${currentRunId}/markdown`);
        if (!response.ok) throw new Error(`Download failed: ${response.status}`);

        const blob = await response.blob();
        const url  = window.URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `blog_${currentRunId}.md`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast('Download started', 'success');

    } catch (error) {
        showToast('Download failed', 'error');
    }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName + 'Tab').classList.add('active');
}

function showScreen(screenName) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenName + 'Screen').classList.add('active');
}

function showToast(message, type = 'success') {
    const toast     = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function addLog(message) {
    const ts = new Date().toISOString();
    logs.push(`[${ts}] ${message}`);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
