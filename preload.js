// Preload script - exposes nothing to renderer for security
// All communication between main and renderer is disabled by default
const { contextBridge } = require('electron');

// Expose any needed APIs here (currently none needed)
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
});
