const path = require("path");
const { app, BrowserWindow, ipcMain } = require("electron");

const {
  connectIntegration,
  syncIntegration,
  listConnections,
  disconnectIntegration,
  listProviders
} = require("./integrations/service.cjs");

function createWindow() {
  const win = new BrowserWindow({
    width: 1180,
    height: 760,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  const devUrl = process.env.VITE_DEV_SERVER_URL;
  if (devUrl) win.loadURL(devUrl);
  else win.loadFile(path.join(__dirname, "..", "dist", "index.html"));

  return win;
}

app.whenReady().then(() => {
  ipcMain.handle("integrations:providers", async () => listProviders());
  ipcMain.handle("integrations:connect", async (_evt, payload) => connectIntegration(payload));
  ipcMain.handle("integrations:list", async () => listConnections());
  ipcMain.handle("integrations:sync", async (_evt, connectionId) => syncIntegration(connectionId));
  ipcMain.handle("integrations:disconnect", async (_evt, connectionId) => disconnectIntegration(connectionId));

  createWindow();
});
