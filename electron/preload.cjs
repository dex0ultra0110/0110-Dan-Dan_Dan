const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("danIntegrations", {
  providers: () => ipcRenderer.invoke("integrations:providers"),
  connect: (payload) => ipcRenderer.invoke("integrations:connect", payload),
  list: () => ipcRenderer.invoke("integrations:list"),
  sync: (connectionId) => ipcRenderer.invoke("integrations:sync", connectionId),
  disconnect: (connectionId) => ipcRenderer.invoke("integrations:disconnect", connectionId)
});
