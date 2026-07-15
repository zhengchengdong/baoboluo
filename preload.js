// Preload script - exposes minimal API to renderer for security
const { contextBridge, ipcRenderer } = require('electron');

// 弹幕服务器配置（和 WssBarrageServer.exe.config 里的 wsListenPort 保持一致）
const BARRAGE_WS_PORT = 8888;

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  // 弹幕 WebSocket 地址，H5 游戏里直接 new WebSocket('ws://127.0.0.1:8888') 即可
  barrageWsUrl: `ws://127.0.0.1:${BARRAGE_WS_PORT}`,
  barragePort: BARRAGE_WS_PORT,
  // 监听弹幕消息（来自主进程 IPC）
  onBarrage: (callback) => {
    ipcRenderer.on('barrage', (_event, msg) => callback(msg));
  },
});
