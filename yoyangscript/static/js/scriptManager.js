class ScriptManager {
    constructor() {
        this.scripts = [];
        this.batchMode = false;
        this.selected = new Set();
    }
    async load() {
        const data = await Api.getScripts();
        this.scripts = data.scripts || [];
        this.selected.clear();
    }
    async upload(file) {
        await Api.uploadScript(file);
        await this.load();
    }
    async deleteOne(name) {
        await Api.deleteScript(name);
        await this.load();
    }
    async deleteSelected() {
        const tasks = [...this.selected].map(n => Api.deleteScript(n));
        await Promise.all(tasks);
        await this.load();
        this.selected.clear();
    }
    toggleBatch() {
        this.batchMode = !this.batchMode;
        if (!this.batchMode) this.selected.clear();
    }
    toggleSelect(name) {
        this.selected.has(name) ? this.selected.delete(name) : this.selected.add(name);
    }
    async run(name) {
        return await Api.runScript(name);
    }
}