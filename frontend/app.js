// State
let currentRunId = null;
let pollingInterval = null;
const logs = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set today's date
    document.getElementById('asOf').value = new Date().toISOString().split('T')[0];
    
    // Event listeners
    document.getElementById('blogForm').addEventListener('submit', handleFormSubmit);
    document.getElementById('downloadBtn').addEventListener('click', downloadMarkdown);
    
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Load past blogs on startup
    loadPastBlogs();
});

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const topic = document.getElementById('topic').value.trim();
    const asOf = document.getElementById('asOf').value;
    
    if (!topic) {
        showToast('Please enter a topic', 'error');
        return;
    }
    
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.textContent = 'Generating...';
    
    try {
        // Call API to start generation
        const response = await fetch('/api/v1/blog/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, as_of: asOf })
        });
        
        if (!response.ok) throw new Error('Failed to start generation');
        
        const data = await response.json();
        currentRunId = data.run_id;
        
        addLog(`Started generation - Run ID: ${data.run_id}`);
        showScreen('loading');
        startPolling();
        
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
        btn.disabled = false;
        btn.textContent = '🚀 Generate Blog';
    }
}

// Start polling for status
function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);
    
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/v1/blog/status/${currentRunId}`);
            if (!response.ok) throw new Error('Failed to get status');
            
            const data = await response.json();
            
            // ADD THIS: Log status updates
            addLog(`Status: ${data.status} - ${data.message}`);
            if (data.plan) {
                addLog(`Plan created: ${data.plan.blog_title}`);
                addLog(`Tasks: ${data.plan.tasks.length}`);
            }
            if (data.images_count !== undefined) {
                addLog(`Images generated: ${data.images_count}`);
            }
            
            // Update loading message
            document.getElementById('loadingMessage').textContent = data.message || 'Processing...';
            
            // Show progress info if available
            if (data.plan || data.images_count !== undefined) {
                let info = '<div style="font-size: 14px; color: #666;">';
                if (data.mode) info += `<p>Mode: <strong>${data.mode}</strong></p>`;
                if (data.plan) info += `<p>Tasks: <strong>${data.plan.tasks.length}</strong></p>`;
                if (data.images_count !== undefined) info += `<p>Images: <strong>${data.images_count}</strong></p>`;
                info += '</div>';
                document.getElementById('progressInfo').innerHTML = info;
            }
            
            // Check if completed
            if (data.status === 'completed') {
                stopPolling();
                addLog('Generation completed successfully');
                showResults(data);
                loadPastBlogs();
                resetGenerateButton();
            } else if (data.status === 'failed') {
                stopPolling();
                addLog('Generation failed: ' + data.message);
                showToast('Generation failed: ' + data.message, 'error');
                showScreen('welcome');
                resetGenerateButton();
            }
            
        } catch (error) {
            addLog('Error checking status: ' + error.message);
        }
    }, 2000); // Poll every 2 seconds
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

function resetGenerateButton() {
    const btn = document.getElementById('generateBtn');
    btn.disabled = false;
    btn.textContent = '🚀 Generate Blog';
}

// Show results
function showResults(data) {
    showScreen('results');
    
    // Render Plan Tab
    if (data.plan) {
        renderPlan(data.plan);
    }
    
    // Render Preview Tab
    renderPreview(data);
    
    // Render Images Tab
    renderImages(data);
    
    // Render Logs Tab
    document.getElementById('logsContent').value = logs.join('\n\n');
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
        html += '<h3>Tasks</h3>';
        html += '<table class="tasks-table"><thead><tr>';
        html += '<th>ID</th><th>Title</th><th>Words</th><th>Features</th>';
        html += '</tr></thead><tbody>';
        
        plan.tasks.forEach(task => {
            const badges = [];
            if (task.requires_research) badges.push('<span class="task-badge">Research</span>');
            if (task.requires_citations) badges.push('<span class="task-badge">Citations</span>');
            if (task.requires_code) badges.push('<span class="task-badge">Code</span>');
            
            html += `
                <tr>
                    <td>${task.id}</td>
                    <td>${escapeHtml(task.title)}</td>
                    <td>${task.target_words}</td>
                    <td>${badges.join(' ') || '-'}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
    }
    
    document.getElementById('planContent').innerHTML = html;
}

function renderPreview(data) {
    let html = '<p><strong>Blog generated successfully!</strong></p>';
    if (data.markdown_path) {
        html += `<p>File: <code>${escapeHtml(data.markdown_path)}</code></p>`;
    }
    html += '<p>Click the download button above to get the markdown file.</p>';
    
    document.getElementById('previewContent').innerHTML = html;
}

function renderImages(data) {
    let html = '';
    if (data.images_count && data.images_count > 0) {
        html = `<p>${data.images_count} image(s) generated and saved with your blog.</p>`;
    } else {
        html = '<p>No images were generated for this blog.</p>';
    }
    document.getElementById('imagesContent').innerHTML = html;
}

// Load past blogs
async function loadPastBlogs() {
    try {
        const response = await fetch('/api/v1/blog/list');
        if (!response.ok) throw new Error('Failed to load blogs');
        
        const data = await response.json();
        const listEl = document.getElementById('pastBlogsList');
        
        if (!data.blogs || data.blogs.length === 0) {
            listEl.innerHTML = '<p style="color: #999; font-size: 14px;">No past blogs found.</p>';
            return;
        }
        
        // Sort by created_at descending
        const blogs = data.blogs.sort((a, b) => 
            new Date(b.created_at) - new Date(a.created_at)
        );
        
        listEl.innerHTML = blogs.map(blog => {
            const statusClass = `status-${blog.status}`;
            return `
                <div class="blog-item" onclick="loadBlog('${blog.run_id}')">
                    <div class="blog-item-title">${escapeHtml(blog.topic || 'Untitled')}</div>
                    <div class="blog-item-meta">
                        <span class="status-badge ${statusClass}">${blog.status}</span>
                        ${new Date(blog.created_at).toLocaleDateString()}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        document.getElementById('pastBlogsList').innerHTML = 
            '<p style="color: #dc3545;">Error loading blogs</p>';
    }
}

// Load a specific blog
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
        showResults(data);
        
    } catch (error) {
        showToast('Failed to load blog', 'error');
    }
}

// Download markdown
async function downloadMarkdown() {
    if (!currentRunId) {
        showToast('No blog to download', 'error');
        return;
    }
    
    try {
        addLog(`Attempting to download markdown for run: ${currentRunId}`);
        const response = await fetch(`/api/v1/blog/download/${currentRunId}/markdown`);
        
        if (!response.ok) {
            const errorText = await response.text();
            addLog(`Download error: ${response.status} - ${errorText}`);
            throw new Error(`Download failed: ${response.status}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `blog_${currentRunId}.md`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('Download started!', 'success');
    } catch (error) {
        showToast('Download failed', 'error');
    }
}

// Switch tabs
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName + 'Tab').classList.add('active');
}

// Show screen
function showScreen(screenName) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenName + 'Screen').classList.add('active');
}

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Add log
function addLog(message) {
    const timestamp = new Date().toISOString();
    logs.push(`[${timestamp}] ${message}`);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}