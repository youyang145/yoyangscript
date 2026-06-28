class UI {
    constructor(scriptManager, bgManager) {
        this.sm = scriptManager;
        this.bg = bgManager;
        this.grid = document.getElementById('scriptGrid');
        this.toast = document.getElementById('toast');
        this.loader = document.getElementById('loader');
        this.menuBtn = document.getElementById('menuBtn');
        this.menuDropdown = document.getElementById('menuDropdown');
        this.batchBar = document.getElementById('batchBar');
        this.fileInput = document.getElementById('fileInput');
        this.runningBtn = document.getElementById('runningBtn');
        this.runningPanel = document.getElementById('runningPanel');
        this.stopAllBtn = document.getElementById('stopAllBtn');
        this._toastTimer = null;
        this._logTimer = null;
    }

    // 修改showToast：显示2700ms后渐隐（0.3s过渡）
    showToast(msg, duration = 2700) {
        this.toast.textContent = msg;
        this.toast.style.transition = 'opacity 0.3s ease';
        this.toast.classList.add('show');
        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => {
            this.toast.style.opacity = '0';
            setTimeout(() => {
                this.toast.classList.remove('show');
                this.toast.style.opacity = ''; // 移除内联样式
            }, 300);
        }, duration);
    }

    showLoading(show) {
        this.loader.classList.toggle('active', show);
    }

    renderList() {
        const scripts = this.sm.scripts;
        if (scripts.length === 0) {
            this.grid.innerHTML = '<div class="empty-state">📭 还没有脚本，点击右上角菜单添加</div>';
            this.batchBar.style.display = 'none';
            return;
        }
        let html = '';
        scripts.forEach(scr => {
            const safeName = this._escapeHtml(scr.name);
            const sizeKB = (scr.size / 1024).toFixed(1) + ' KB';
            const checked = this.sm.selected.has(scr.name) ? 'checked' : '';
            const batchDisplay = this.sm.batchMode ? 'block' : 'none';
            html += `
            <div class="script-card" data-name="${safeName}">
                <input type="checkbox" class="batch-check" ${checked} style="display:${batchDisplay};">
                <div class="icon">📜</div>
                <div class="name">${safeName}</div>
                <div class="size">${sizeKB}</div>
                <div class="actions">
                    <button class="btn btn-sm run-btn">▶️ 运行</button>
                    <button class="btn btn-sm btn-danger delete-btn">✕</button>
                </div>
            </div>`;
        });
        this.grid.innerHTML = html;
        this.batchBar.style.display = this.sm.batchMode ? 'flex' : 'none';
    }

    bindEvents() {
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const pageId = 'page-' + btn.dataset.page;
                document.querySelectorAll('.main-content').forEach(p => p.style.display = 'none');
                document.getElementById(pageId).style.display = 'block';
            });
        });
        this.menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.menuDropdown.classList.toggle('show');
        });
        document.addEventListener('click', (e) => {
            if (!this.menuBtn.contains(e.target) && !this.menuDropdown.contains(e.target))
                this.menuDropdown.classList.remove('show');
        });
        document.getElementById('menuAddScript').addEventListener('click', () => {
            this.fileInput.click(); this.menuDropdown.classList.remove('show');
        });
        const changeBgHandler = async () => {
            const result = await BgManager.promptFile();
            if (!result) return;
            this.showLoading(true);
            try {
                const serverUrl = await Api.uploadBackground(result.file);
                BgManager.apply(serverUrl);
                BgManager.save(serverUrl);
                this.showToast('🖼️ 背景已更新，所有设备同步');
            } catch (err) {
                console.error(err);
                BgManager.apply(result.dataUrl);
                BgManager.save(result.dataUrl);
                this.showToast('⚠️ 背景仅保存到本机（服务器不可用）');
            } finally {
                this.showLoading(false);
            }
        };
        document.getElementById('menuChangeBg').addEventListener('click', () => {
            this.menuDropdown.classList.remove('show');
            changeBgHandler();
        });
        document.getElementById('userChangeBg').addEventListener('click', changeBgHandler);
        document.getElementById('menuBatchManage').addEventListener('click', () => {
            this.sm.toggleBatch(); this.renderList(); this.menuDropdown.classList.remove('show');
        });
        document.getElementById('menuCheckUpdate').addEventListener('click', () => {
            this.menuDropdown.classList.remove('show');
            this.showToast('🔍 正在检查更新...');
            this.checkUpdate(false);  // silent=false，显示结果提示
        });
        this.fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            this.showLoading(true);
            try {
                await this.sm.upload(file);
                this.renderList();
                this.showToast('✅ 上传成功');
            } catch (err) {
                this.showToast('❌ ' + err.message);
            } finally {
                this.showLoading(false);
                this.fileInput.value = '';
            }
        });
        this.grid.addEventListener('click', async (e) => {
            const card = e.target.closest('.script-card');
            if (!card) return;
            const name = card.dataset.name;
            if (e.target.classList.contains('delete-btn')) {
                if (!confirm(`确定要删除 “${name}” 吗？`)) return;
                this.showLoading(true);
                try {
                    await this.sm.deleteOne(name);
                    this.renderList();
                    this.showToast(`🗑️ 已删除 “${name}”`);
                } catch (err) { this.showToast('❌ ' + err.message); }
                finally { this.showLoading(false); }
            } else if (e.target.classList.contains('run-btn')) {
                this.showLoading(true);
                try {
                    const res = await this.sm.run(name);
                    if (res.started) {
                        this.showToast(`🚀 已启动: ${name}`);
                        this.showLogPanel(res.log_id);
                    } else this.showToast('⚠️ 启动失败');
                } catch (err) { this.showToast('❌ ' + err.message); }
                finally { this.showLoading(false); }
            } else if (e.target.classList.contains('batch-check')) {
                this.sm.toggleSelect(name);
                card.querySelector('.batch-check').checked = this.sm.selected.has(name);
            }
        });
        document.getElementById('batchDeleteBtn').addEventListener('click', async () => {
            if (this.sm.selected.size === 0) { this.showToast('⚠️ 请先勾选要删除的脚本'); return; }
            const count = this.sm.selected.size;
            if (!confirm(`确定要删除选中的 ${count} 个脚本吗？`)) return;
            this.showLoading(true);
            try {
                await this.sm.deleteSelected();
                this.sm.batchMode = false;
                this.renderList();
                this.showToast(`🗑️ 已删除 ${count} 个脚本`);
            } catch (err) { this.showToast('❌ ' + err.message); }
            finally { this.showLoading(false); }
        });
        document.getElementById('cancelBatchBtn').addEventListener('click', () => {
            this.sm.toggleBatch(); this.renderList();
        });

        // 🆕 运行中按钮事件
        this.runningBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleRunningPanel();
        });
        document.addEventListener('click', (e) => {
            if (!this.runningBtn.contains(e.target) && !this.runningPanel.contains(e.target)) {
                this.runningPanel.classList.remove('show');
            }
        });

        // 🆕 停止全部脚本按钮
        this.stopAllBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm('确定要停止所有运行中的脚本吗？')) return;
            try {
                const result = await Api.stopAllScripts();
                this.showToast(`🗑️ 已停止 ${result.stopped} 个脚本`);
                // 同步更新运行面板
                if (this.runningPanel.classList.contains('show')) {
                    this.toggleRunningPanel();
                }
            } catch (err) {
                this.showToast('❌ 停止失败: ' + err.message);
            }
        });
    }

    // 🆕 切换运行面板显示，并刷新列表
    async toggleRunningPanel() {
        if (this.runningPanel.classList.contains('show')) {
            this.runningPanel.classList.remove('show');
            return;
        }
        try {
            const scripts = await Api.getRunningScripts();
            let html = '';
            if (scripts.length === 0) {
                html = '<div style="padding:12px; opacity:0.7;">暂无运行中的脚本</div>';
            } else {
                scripts.forEach(name => {
                    html += `<div style="padding:8px 12px; border-bottom:1px solid rgba(255,255,255,0.1);">📜 ${this._escapeHtml(name)}</div>`;
                });
            }
            this.runningPanel.innerHTML = html;
            this.runningPanel.classList.add('show');
        } catch (e) {
            this.showToast('❌ 无法获取运行列表');
        }
    }

    showLogPanel(logId) {
        const oldPanel = document.getElementById('log-panel');
        if (oldPanel) {
            clearTimeout(this._logTimer);
            this._dismissLogPanel(oldPanel);
        }
        const panel = document.createElement('div');
        panel.id = 'log-panel';
        panel.style.opacity = '1';
        panel.style.transition = 'opacity 0.5s ease';
        panel.textContent = '加载日志中...';
        // 点击面板可提前关闭
        panel.style.cursor = 'pointer';
        panel.title = '点击关闭';
        panel.addEventListener('click', () => this._dismissLogPanel(panel));
        document.body.appendChild(panel);

        const dismiss = () => { this._dismissLogPanel(panel); };
        let settled = false;
        let pollCount = 0;
        const MAX_POLL = 3;  // 最多轮询 3 次（6 秒）

        const updateLog = async () => {
            if (settled) return;
            pollCount++;
            try {
                const data = await Api.getScriptOutput(logId);
                const output = data.output || '';
                panel.textContent = output || '(无输出)';
                const finished = output && output.includes('=== 结束 ===');
                if (finished || pollCount >= MAX_POLL) {
                    settled = true;
                    this._logTimer = setTimeout(dismiss, 2000);
                } else {
                    this._logTimer = setTimeout(updateLog, 2000);
                }
            } catch (e) {
                panel.textContent = '日志加载失败';
                settled = true;
                this._logTimer = setTimeout(dismiss, 2000);
            }
        };
        updateLog();
    }

    _dismissLogPanel(panel) {
        clearTimeout(this._logTimer);
        panel.style.opacity = '0';
        setTimeout(() => {
            if (panel.parentNode) panel.parentNode.removeChild(panel);
        }, 500);
    }

    async checkUpdate(silent = true) {
        try {
            const info = await Api.checkUpdate(false);
            if (info.error) {
                if (!silent) this.showToast('⚠️ ' + info.error);
                return;
            }
            if (info.has_update) {
                const latest = info.latest_version;
                const ignored = localStorage.getItem('update_ignored');
                if (ignored) {
                    const data = JSON.parse(ignored);
                    if (data.version === latest && Date.now() < data.until) return;
                }
                this.showUpdateModal(info);
            } else if (!silent) {
                this.showToast('✅ 已是最新版本 v' + info.current_version);
            }
        } catch (e) {
            if (!silent) this.showToast('❌ 检查更新失败');
            console.warn('更新检查失败', e);
        }
    }

    showUpdateModal(info) {
        const modal = document.getElementById('update-modal');
        document.getElementById('update-title').textContent = '🔔 发现新版本';
        document.getElementById('update-current').textContent = 'v' + info.current_version;
        document.getElementById('update-latest').textContent = 'v' + info.latest_version;
        const changelog = info.changelog
            ? info.changelog.replace(/\n/g, '<br>')
            : '无更新说明';
        document.getElementById('update-content').innerHTML = changelog;
        if (info.published_at) {
            document.getElementById('update-date').textContent = '发布于 ' + info.published_at.slice(0, 10);
            document.getElementById('update-date').style.display = '';
        } else {
            document.getElementById('update-date').style.display = 'none';
        }
        modal.style.display = 'flex';

        // 取消按钮
        document.getElementById('update-cancel').onclick = () => {
            modal.style.display = 'none';
            if (document.getElementById('update-ignore-5days').checked) {
                const until = Date.now() + 5 * 24 * 60 * 60 * 1000;
                localStorage.setItem('update_ignored', JSON.stringify({
                    version: info.latest_version,
                    until: until
                }));
            }
        };

        // 立即更新按钮
        const updateBtn = document.getElementById('update-do');
        updateBtn.textContent = '立即更新';
        updateBtn.onclick = async () => {
            updateBtn.textContent = '⏳ 下载中...';
            updateBtn.disabled = true;
            try {
                const result = await Api.applyUpdate();
                if (result.success) {
                    updateBtn.textContent = '✅ 更新完成';
                    document.getElementById('update-content').innerHTML =
                        `<b>${result.message}</b><br><br>
                        已更新 <b>${result.updated_files}</b> 个文件。<br>
                        <span style="color:#ffc107;">⚠️ 请关闭程序后重新启动以生效。</span>`;
                } else {
                    updateBtn.textContent = '❌ 更新失败';
                    document.getElementById('update-content').innerHTML =
                        `<b>${result.message}</b><br><br>
                        <a href="${info.download_url || '#'}" target="_blank" style="color:#4f7df3;">点击手动下载</a>`;
                }
            } catch (e) {
                updateBtn.textContent = '❌ 失败';
                document.getElementById('update-content').innerHTML +=
                    `<br><br><span style="color:#e74c4c;">网络错误，请重试或手动下载</span>`;
            }
            updateBtn.disabled = false;
        };

        // 手动下载链接（兜底）
        document.getElementById('update-manual').onclick = () => {
            window.open(info.download_url || '#', '_blank');
        };
    }

    async showVersionInfo() {
        try {
            const info = await Api.getVersion();
            this.showToast('YoyangScript v' + info.version);
        } catch (e) {
            // ignore
        }
    }

    async init() {
        await BgManager.initFromServer();
        BgManager.startAutoSync(10000);
        this.bindEvents();
        this.showLoading(true);
        try {
            await this.sm.load();
            this.renderList();
        } catch (err) {
            this.showToast('❌ 无法加载脚本列表: ' + err.message);
        } finally {
            this.showLoading(false);
        }
        // 显示版本号
        try {
            const ver = await Api.getVersion();
            const el = document.getElementById('versionDisplay');
            if (el) el.textContent = 'v' + ver.version;
        } catch (e) { /* ignore */ }
        // 后台检查更新（静默模式）
        this.checkUpdate(true);
    }

    _escapeHtml(str) {
        const map = { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' };
        return str.replace(/[&<>"']/g, m => map[m]);
    }
}