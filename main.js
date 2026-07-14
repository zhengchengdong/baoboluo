const { app, BrowserWindow, protocol, net } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const iconv = require('iconv-lite');

// ── 🔑 必须在 app.whenReady() 之前注册自定义协议的权限 ──
// standard: true → 等同于 http 协议，支持 CORS / fetch / import / 相对路径
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'local-app',
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true,
      corsEnabled: true,
      stream: true,
    },
  },
]);

// ── 调试模式：npm start 时开 DevTools，打包后自动关 ──
const isDev = !app.isPackaged;

// ── 🔑 WebGPU 关键开关 ──
app.commandLine.appendSwitch('enable-unsafe-webgpu');
app.commandLine.appendSwitch('ignore-gpu-blocklist');
app.commandLine.appendSwitch('disable-gpu-sandbox');
app.commandLine.appendSwitch('enable-gpu-rasterization');

// 禁用硬件加速 = 彻底没 WebGPU，确认这一行没有被启用：
// app.disableHardwareAcceleration();

let mainWindow = null;
let barrageProcess = null;

// ── 启动抖音弹幕抓取服务 ──
function startBarrageServer() {
  const barrageDir = isDev
    ? path.join(__dirname, 'WssBarrageServer')
    : path.join(process.resourcesPath, 'WssBarrageServer');

  const exePath = path.join(barrageDir, 'WssBarrageServer.exe');

  if (!fs.existsSync(exePath)) {
    console.warn('[弹幕服务] 找不到 WssBarrageServer.exe，跳过启动');
    return;
  }

  console.log('[弹幕服务] 启动中...', exePath);

  barrageProcess = spawn(exePath, [], {
    cwd: barrageDir,
    stdio: 'pipe',
    windowsHide: true,
  });

  barrageProcess.stdout?.on('data', (data) => {
    console.log(`[弹幕] ${iconv.decode(data, 'gbk').trim()}`);
  });

  barrageProcess.stderr?.on('data', (data) => {
    console.error(`[弹幕-错误] ${iconv.decode(data, 'gbk').trim()}`);
  });

  barrageProcess.on('error', (err) => {
    console.error('[弹幕服务] 启动失败:', err.message);
  });

  barrageProcess.on('close', (code) => {
    console.log(`[弹幕服务] 已退出 (code=${code})`);
    barrageProcess = null;
  });
}

function stopBarrageServer() {
  if (barrageProcess && !barrageProcess.killed) {
    console.log('[弹幕服务] 正在关闭...');
    barrageProcess.kill();
    barrageProcess = null;
  }
}

// ── MIME 类型映射 ──
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'text/javascript; charset=utf-8',
  '.json': 'application/json',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.gif':  'image/gif',
  '.glb':  'model/gltf-binary',
  '.gltf': 'model/gltf+json',
  '.bin':  'application/octet-stream',
  '.wasm': 'application/wasm',
  '.css':  'text/css; charset=utf-8',
};

/**
 * 自定义 local-app:// 协议
 * 把 URL 路径映射到 __dirname 下的实际文件，这样 fetch() / import 都能正常工作
 */
function registerLocalProtocol() {
  protocol.handle('local-app', (request) => {
    const reqUrl = new URL(request.url);
    // 路径如 local-app:///node_modules/three/... 或 local-app:///pineapple_CircularBand.html
    let relPath = decodeURIComponent(reqUrl.pathname).replace(/^\/+/, '');
    if (!relPath) relPath = 'pineapple_CircularBand.html';

    // 安全检查：防止目录穿越
    const safePath = path.resolve(path.join(__dirname, relPath));
    if (!safePath.startsWith(path.resolve(__dirname))) {
      return new Response('Forbidden', { status: 403 });
    }

    try {
      const data = fs.readFileSync(safePath);
      const ext = path.extname(safePath).toLowerCase();
      return new Response(data, {
        status: 200,
        headers: {
          'content-type': MIME[ext] || 'application/octet-stream',
          'access-control-allow-origin': '*',
          'cache-control': 'no-cache',
        },
      });
    } catch (e) {
      console.error('[local-app] 404:', relPath);
      return new Response('Not Found: ' + relPath, { status: 404 });
    }
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    title: 'Pineapple Circular Band - GPU PBD',
    backgroundColor: '#111111',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webgl: true,
    },
    autoHideMenuBar: true,
  });

  // ── 通过自定义协议加载，这样所有 fetch / import / 资源加载都走 local-app:// 协议 ──
  mainWindow.loadURL('local-app:///pineapple_CircularBand.html');

  // ★ 调试模式：自动打开 DevTools，可以看到报错
  if (isDev) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  // 监听 console 消息，转发到主进程终端（方便调试）
  mainWindow.webContents.on('console-message', (event, level, message) => {
    const prefix = ['','⚠','❌'][level] || '';
    console.log(`[renderer] ${prefix}${message}`);
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  // ── 打印 GPU 信息（帮助诊断 WebGPU 问题）──
  try {
    const gpuInfo = await app.getGPUInfo('basic');
    console.log('[GPU Info]', JSON.stringify(gpuInfo, null, 2));
  } catch (e) {
    console.log('[GPU Info] 获取失败:', e.message);
  }

  registerLocalProtocol();
  createWindow();

  // 启动弹幕抓取服务
  startBarrageServer();
});

// 应用退出时关闭弹幕服务
app.on('before-quit', () => {
  stopBarrageServer();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
