class BgManager {
    // 默认背景（一张深色抽象渐变，看起来像星空）
    static DEFAULT_BG = 'url(data:image/svg+xml,' + encodeURIComponent(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"><defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#1a1a2e"/><stop offset="50%" stop-color="#16213e"/><stop offset="100%" stop-color="#0f3460"/></linearGradient></defs><rect width="800" height="600" fill="url(#g)"/><circle cx="100" cy="80" r="2" fill="rgba(255,255,255,0.5)"/><circle cx="300" cy="150" r="1.5" fill="rgba(255,255,255,0.4)"/><circle cx="600" cy="200" r="2.5" fill="rgba(255,255,255,0.6)"/><circle cx="750" cy="100" r="1" fill="rgba(255,255,255,0.3)"/><circle cx="200" cy="400" r="2" fill="rgba(255,255,255,0.5)"/><circle cx="500" cy="500" r="1.5" fill="rgba(255,255,255,0.4)"/></svg>') + ')';

    static async initFromServer() {
        try {
            const url = await Api.getBackground();
            if (url) {
                BgManager.apply(url);
                try { localStorage.setItem('customBg', url); } catch(e){}
                return;
            }
        } catch(e) { console.warn('从服务器获取背景失败，回退本地'); }
        BgManager.loadFromLocal();
    }

    static apply(url) {
        document.body.style.background = `url(${url}) center / cover no-repeat fixed`;
    }

    static save(url) {
        try { localStorage.setItem('customBg', url); } catch(e){}
    }

    static loadFromLocal() {
        try {
            const saved = localStorage.getItem('customBg');
            if (saved) {
                BgManager.apply(saved);
            } else {
                // 没有自定义背景，应用默认背景
                document.body.style.background = BgManager.DEFAULT_BG + ' center / cover no-repeat fixed';
            }
        } catch(e) {
            document.body.style.background = BgManager.DEFAULT_BG + ' center / cover no-repeat fixed';
        }
    }

    static async promptFile() {
        return new Promise(resolve => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (!file) { resolve(null); return; }
                const reader = new FileReader();
                reader.onload = (ev) => {
                    resolve({ file, dataUrl: ev.target.result });
                };
                reader.readAsDataURL(file);
            };
            input.click();
        });
    }

    static async startAutoSync(interval = 10000) {
        let lastKnown = 0;
        try { lastKnown = await Api.getBgLastModified(); } catch(e) { return; }
        setInterval(async () => {
            try {
                const serverTime = await Api.getBgLastModified();
                if (serverTime > lastKnown) {
                    const url = await Api.getBackground();
                    if (url) {
                        BgManager.apply(url);
                        BgManager.save(url);
                    }
                    lastKnown = serverTime;
                }
            } catch(e) {}
        }, interval);
    }
}