const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

const isDev = !app.isPackaged;

let mainWindow = null;
let overlayWindow = null;

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    titleBarStyle: 'hidden',
    backgroundColor: '#09090b', // zinc-950
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../frontend/dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  return mainWindow;
}

function createAvatarOverlay() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenW, height: screenH } = primaryDisplay.workAreaSize;

  const W = 280;
  const H = 380;
  const posX = Math.max(0, screenW - W - 20);
  const posY = Math.max(0, screenH - H - 20);

  overlayWindow = new BrowserWindow({
    width: W,
    height: H,
    x: posX,
    y: posY,
    alwaysOnTop: true,
    frame: false,
    transparent: true,
    resizable: false,
    skipTaskbar: true,
    hasShadow: false,
    backgroundColor: '#00000000',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Ensure overlay floats on top of all windows and workspaces
  overlayWindow.setAlwaysOnTop(true, 'screen-saver');
  try {
    overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  } catch (e) {}

  if (isDev) {
    overlayWindow.loadURL('http://localhost:5173/avatar-overlay.html');
  } else {
    overlayWindow.loadFile(path.join(__dirname, '../../frontend/dist/avatar-overlay.html'));
  }

  overlayWindow.on('closed', () => {
    overlayWindow = null;
  });

  // Reposition if screen resolution changes
  screen.on('display-metrics-changed', () => {
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      try {
        const { width, height } = screen.getPrimaryDisplay().workAreaSize;
        overlayWindow.setPosition(Math.max(0, width - W - 20), Math.max(0, height - H - 20));
      } catch (e) {}
    }
  });

  return overlayWindow;
}

app.whenReady().then(() => {
  createMainWindow();
  createAvatarOverlay();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
      createAvatarOverlay();
    }
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// Secure IPC Handlers
ipcMain.handle('ping', () => 'pong');
