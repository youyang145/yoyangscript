class Api {
    static async getScripts() {
        const res = await fetch('/list_scripts');
        if (!res.ok) throw new Error(`请求失败 (${res.status})`);
        return await res.json();
    }
    static async uploadScript(file) {
        const form = new FormData();
        form.append('script_file', file);
        const res = await fetch('/upload_script', { method: 'POST', body: form });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || '上传失败');
        return data;
    }
    static async deleteScript(name) {
        const res = await fetch('/delete_script', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ script: name })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || '删除失败');
        return data;
    }
    static async runScript(name) {
        const res = await fetch('/run_script', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ script: name })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || '启动失败');
        return data;
    }
    static async getScriptOutput(logId) {
        const res = await fetch(`/script_output?log_id=${encodeURIComponent(logId)}`);
        if (!res.ok) throw new Error('加载日志失败');
        return await res.json();
    }
    static async getBackground() {
        const res = await fetch('/api/get-background');
        if (!res.ok) throw new Error('获取背景失败');
        const data = await res.json();
        return data.bg_url;
    }
    static async uploadBackground(file) {
        const form = new FormData();
        form.append('bg_file', file);
        const res = await fetch('/api/set-background', { method: 'POST', body: form });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || '上传背景失败');
        return data.bg_url;
    }
    static async getBgLastModified() {
        const res = await fetch('/api/bg-last-modified');
        if (!res.ok) throw new Error('获取背景更新时间失败');
        const data = await res.json();
        return data.last_modified;
    }
    static async checkUpdate(force = false) {
        const url = force ? '/api/check-update?force=1' : '/api/check-update';
        const res = await fetch(url);
        if (!res.ok) throw new Error('检查更新失败');
        return await res.json();
    }
    static async getVersion() {
        const res = await fetch('/api/version');
        if (!res.ok) throw new Error('获取版本失败');
        return await res.json();
    }
    static async applyUpdate() {
        const res = await fetch('/api/apply-update', { method: 'POST' });
        if (!res.ok) throw new Error('更新失败');
        return await res.json();
    }
    static async getRunningScripts() {
        const res = await fetch('/running_scripts');
        if (!res.ok) throw new Error('获取运行列表失败');
        const data = await res.json();
        return data.scripts;
    }
    static async stopAllScripts() {
        const res = await fetch('/stop_all_scripts', { method: 'POST' });
        if (!res.ok) throw new Error('停止脚本失败');
        return await res.json();
    }
}