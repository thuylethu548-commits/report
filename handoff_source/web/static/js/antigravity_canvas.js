/**
 * Antigravity 2.0 Web Agentic Canvas — Client Logic
 * Coordinates 3-Panel Split Layout, File Editor Check, Live Artifacts, and Agent Chat Stream.
 */

// State
let currentOpenFile = "data/storage.py";
let activeTab = "editor"; // editor | artifact | preview
let isDraggingSplitter = null;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initSplitters();
    loadWorkspaceTree();
    loadModelsQuota();
    loadFileContent(currentOpenFile);
    setupChatEvents();
});

/* ==========================================================================
   1. Splitter Drag Resize Handling
   ========================================================================== */
function initSplitters() {
    const split1 = document.getElementById('splitter-1');
    const split2 = document.getElementById('splitter-2');
    const panelSidebar = document.getElementById('panel-sidebar');
    const panelAux = document.getElementById('panel-auxiliary');

    if (split1 && panelSidebar) {
        split1.addEventListener('mousedown', (e) => {
            isDraggingSplitter = 'split1';
            split1.classList.add('active');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });
    }

    if (split2 && panelAux) {
        split2.addEventListener('mousedown', (e) => {
            isDraggingSplitter = 'split2';
            split2.classList.add('active');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });
    }

    window.addEventListener('mousemove', (e) => {
        if (!isDraggingSplitter) return;

        if (isDraggingSplitter === 'split1') {
            const newWidth = Math.max(180, Math.min(e.clientX, 450));
            panelSidebar.style.width = `${newWidth}px`;
        } else if (isDraggingSplitter === 'split2') {
            const newWidth = Math.max(280, Math.min(window.innerWidth - e.clientX, 850));
            panelAux.style.width = `${newWidth}px`;
        }
    });

    window.addEventListener('mouseup', () => {
        if (isDraggingSplitter) {
            if (split1) split1.classList.remove('active');
            if (split2) split2.classList.remove('active');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            isDraggingSplitter = null;
        }
    });
}

/* ==========================================================================
   2. Panel 1: Workspace Tree & Quota Telemetry
   ========================================================================== */
async function loadWorkspaceTree() {
    const container = document.getElementById('tree-container');
    if (!container) return;

    try {
        const resp = await fetch('/api/v1/canvas/workspace-tree');
        if (!resp.ok) return;
        const data = await resp.json();

        container.innerHTML = renderTreeNodes(data.tree);
    } catch (e) {
        console.warn('Failed to load workspace tree:', e);
    }
}

function renderTreeNodes(nodes) {
    if (!nodes || nodes.length === 0) return '';
    return nodes.map(node => {
        if (node.type === 'dir') {
            return `
                <div class="agy-tree-dir">
                    <div class="agy-tree-node" onclick="toggleTreeNode(this)">
                        <span style="font-size: 11px;">📁</span>
                        <span>${escapeHtml(node.name)}</span>
                    </div>
                    <div class="agy-tree-children" style="display: block;">
                        ${renderTreeNodes(node.children)}
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="agy-tree-node" onclick="openFileInEditor('${escapeHtml(node.path)}')">
                    <span style="font-size: 11px;">📄</span>
                    <span>${escapeHtml(node.name)}</span>
                </div>
            `;
        }
    }).join('');
}

function toggleTreeNode(el) {
    const children = el.nextElementSibling;
    if (children) {
        const isHidden = children.style.display === 'none';
        children.style.display = isHidden ? 'block' : 'none';
        el.querySelector('span').textContent = isHidden ? '📁' : '📂';
    }
}

async function loadModelsQuota() {
    const container = document.getElementById('quota-container');
    if (!container) return;

    try {
        const resp = await fetch('/api/v1/canvas/models-quota');
        if (!resp.ok) return;
        const data = await resp.json();

        container.innerHTML = (data.providers || []).map(p => `
            <div class="agy-quota-row">
                <span class="agy-quota-name">
                    <span style="width: 6px; height: 6px; border-radius: 50%; background: ${p.badge_color};"></span>
                    ${escapeHtml(p.name)}
                </span>
                <span class="agy-quota-val" style="color: ${p.badge_color};">${p.weekly_limit_remaining}</span>
            </div>
        `).join('');
    } catch (e) {
        console.warn('Failed to load models quota:', e);
    }
}

/* ==========================================================================
   3. Panel 3: Auxiliary Editor Check & Live Artifacts
   ========================================================================== */
function switchAuxTab(tab) {
    activeTab = tab;
    document.querySelectorAll('.agy-aux-tab').forEach(t => {
        t.classList.toggle('active', t.getAttribute('data-tab') === tab);
    });

    const editorPane = document.getElementById('pane-editor');
    const artifactPane = document.getElementById('pane-artifact');
    const previewPane = document.getElementById('pane-preview');

    if (editorPane) editorPane.style.display = tab === 'editor' ? 'flex' : 'none';
    if (artifactPane) artifactPane.style.display = tab === 'artifact' ? 'flex' : 'none';
    if (previewPane) previewPane.style.display = tab === 'preview' ? 'flex' : 'none';
}

function openFileInEditor(filePath) {
    currentOpenFile = filePath;
    switchAuxTab('editor');
    loadFileContent(filePath);
}

async function loadFileContent(filePath) {
    const editorTextarea = document.getElementById('editor-textarea');
    const filePathLabel = document.getElementById('editor-filepath-label');
    const fileLangLabel = document.getElementById('editor-lang-label');

    if (filePathLabel) filePathLabel.textContent = filePath;

    try {
        const resp = await fetch(`/api/v1/canvas/file-content?path=${encodeURIComponent(filePath)}`);
        if (!resp.ok) {
            if (editorTextarea) editorTextarea.value = `// Không thể tải file: ${filePath}`;
            return;
        }
        const data = await resp.json();
        if (editorTextarea) editorTextarea.value = data.content;
        if (fileLangLabel) fileLangLabel.textContent = data.language.toUpperCase();
    } catch (e) {
        console.warn('Failed to load file content:', e);
    }
}

async function saveCurrentFile() {
    const editorTextarea = document.getElementById('editor-textarea');
    const saveBtn = document.getElementById('btn-save-file');
    if (!editorTextarea || !currentOpenFile) return;

    if (saveBtn) saveBtn.textContent = 'Đang lưu...';

    try {
        const resp = await fetch('/api/v1/canvas/file-save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_path: currentOpenFile,
                content: editorTextarea.value
            })
        });
        const data = await resp.json();
        if (resp.ok) {
            if (saveBtn) {
                saveBtn.textContent = '✅ Đã lưu!';
                setTimeout(() => { saveBtn.textContent = '💾 Lưu File'; }, 1800);
            }
        } else {
            alert(`Lỗi: ${data.detail || 'Không thể lưu file'}`);
            if (saveBtn) saveBtn.textContent = '💾 Lưu File';
        }
    } catch (e) {
        alert('Lỗi kết nối khi lưu file');
        if (saveBtn) saveBtn.textContent = '💾 Lưu File';
    }
}

function refreshPreview() {
    const iframe = document.getElementById('preview-iframe');
    const urlInput = document.getElementById('preview-url-input');
    if (iframe && urlInput) {
        iframe.src = urlInput.value;
    }
}

/* ==========================================================================
   4. Panel 2: Agent Chat Execution & Interactive Cards
   ========================================================================== */
function setupChatEvents() {
    const textarea = document.getElementById('chat-input');
    const sendBtn = document.getElementById('btn-send-chat');

    if (textarea) {
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitChatPrompt();
            }
        });
        // Auto-expand textarea
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 180) + 'px';
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', submitChatPrompt);
    }
}

function insertSlashCommand(cmd) {
    const textarea = document.getElementById('chat-input');
    if (textarea) {
        textarea.value = cmd + ' ';
        textarea.focus();
    }
}

async function submitChatPrompt() {
    const textarea = document.getElementById('chat-input');
    const modelSelector = document.getElementById('model-selector');
    const messagesWrap = document.getElementById('chat-messages');

    if (!textarea || !textarea.value.trim() || !messagesWrap) return;

    const prompt = textarea.value.trim();
    const model = modelSelector ? modelSelector.value : 'deepseek-v4-flash';
    textarea.value = '';
    textarea.style.height = '48px';

    // 1. Append User Message
    const userMsgHtml = `
        <div class="agy-msg-user">
            ${escapeHtml(prompt).replace(/\n/g, '<br>')}
        </div>
    `;
    messagesWrap.insertAdjacentHTML('beforeend', userMsgHtml);
    messagesWrap.scrollTop = messagesWrap.scrollHeight;

    // 2. Append Loading Placeholder for Agent
    const loadingId = 'agent-msg-' + Date.now();
    const loadingHtml = `
        <div class="agy-msg-agent" id="${loadingId}">
            <div class="agy-thought-box">
                <div class="agy-thought-header">
                    <span>🧠</span>
                    <span>Đang tư duy & lập kế hoạch tác tử (${escapeHtml(model)})...</span>
                </div>
            </div>
        </div>
    `;
    messagesWrap.insertAdjacentHTML('beforeend', loadingHtml);
    messagesWrap.scrollTop = messagesWrap.scrollHeight;

    try {
        const resp = await fetch('/api/v1/canvas/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, model })
        });
        const data = await resp.json();
        const msgEl = document.getElementById(loadingId);
        if (!msgEl) return;

        // Render Action Summary Card (Antigravity Style)
        let actionCardHtml = '';
        if (data.actions && data.actions.length > 0) {
            actionCardHtml = `
                <div class="agy-action-summary-card">
                    <div class="agy-action-chips">
                        <span class="agy-chip-stat">⚡ Explored 4 files, ran 2 tasks</span>
                        ${(data.files_changed || []).map(fc => `
                            <span class="agy-chip-diff" title="Click để xem diff trên Panel 3" onclick="openFileInEditor('${escapeHtml(fc.name)}')">
                                📝 ${escapeHtml(fc.name)} <strong>${fc.diff}</strong>
                            </span>
                        `).join('')}
                    </div>
                    <button class="agy-btn-top" onclick="switchAuxTab('editor')" style="font-size: 10px; padding: 2px 7px;">Review Code</button>
                </div>
            `;
        }

        // Render Thoughts
        let thoughtsHtml = '';
        if (data.thoughts && data.thoughts.length > 0) {
            thoughtsHtml = `
                <div class="agy-thought-box">
                    <div class="agy-thought-header">
                        <span>🧠</span>
                        <span>Dòng suy nghĩ tác tử (${escapeHtml(data.model_used)})</span>
                    </div>
                    ${data.thoughts.map(t => `<div style="font-size: 11px; opacity: 0.85;">• ${escapeHtml(t)}</div>`).join('')}
                </div>
            `;
        }

        // Render Content Body
        const bodyHtml = `
            <div class="agy-agent-body">
                ${formatMarkdownSimple(data.content)}
            </div>
        `;

        msgEl.innerHTML = actionCardHtml + thoughtsHtml + bodyHtml;
        messagesWrap.scrollTop = messagesWrap.scrollHeight;

    } catch (e) {
        const msgEl = document.getElementById(loadingId);
        if (msgEl) {
            msgEl.innerHTML = `<div style="color: #ef4444; font-size: 12px;">❌ Lỗi thực thi agent: ${escapeHtml(e.message || String(e))}</div>`;
        }
    }
}

function formatMarkdownSimple(text) {
    if (!text) return '';
    let formatted = escapeHtml(text)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    return `<p>${formatted}</p>`;
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
