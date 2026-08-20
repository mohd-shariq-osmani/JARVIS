const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

const isDev = !app.isPackaged;

// ── Main JARVIS Window ────────────────────────────────────────────────────────
function createMainWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    titleBarStyle: 'hidden',
    backgroundColor: '#09090b',
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../frontend/dist/index.html'));
  }

  return mainWindow;
}

// ── Floating Avatar Overlay Window ───────────────────────────────────────────
function createAvatarOverlay() {
  const { width: sw, height: sh } = screen.getPrimaryDisplay().workAreaSize;

  const W = 280;
  const H = 380;

  const overlayWindow = new BrowserWindow({
    width: W,
    height: H,
    // Bottom-right corner, 16px from edge
    x: sw - W - 16,
    y: sh - H - 16,

    // Floating over everything
    alwaysOnTop: true,
    frame: false,
    transparent: true,
    skipTaskbar: true,       // hide from taskbar
    resizable: false,
    hasShadow: false,

    // Required for proper transparency & click-through on Windows
    backgroundColor: '#00000000',

    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      // Allow loading from localhost (dev) or local files (prod)
    },
  });

  // Enable click-through on transparent (non-canvas) areas
  overlayWindow.setIgnoreMouseEvents(false); // let iframe/canvas receive events

  // Load the avatar overlay page
  if (isDev) {
    overlayWindow.loadURL('http://localhost:5173/avatar-overlay.html');
  } else {
    overlayWindow.loadFile(
      path.join(__dirname, '../../frontend/dist/avatar-overlay.html')
    );
  }

  // Keep always-on-top across workspace switches and fullscreen apps
  overlayWindow.setAlwaysOnTop(true, 'screen-saver');

  // Restore position after display changes
  screen.on('display-metrics-changed', () => {
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;
    overlayWindow.setPosition(width - W - 16, height - H - 16);
  });

  return overlayWindow;
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  createMainWindow();
  createAvatarOverlay();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
      createAvatarOverlay();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// Secure IPC
ipcMain.handle('ping', () => 'pong');
