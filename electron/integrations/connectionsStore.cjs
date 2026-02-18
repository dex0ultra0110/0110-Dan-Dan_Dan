const ElectronStore = require("electron-store");

const Store = ElectronStore.default || ElectronStore;
const store = new Store({ name: "dandadan-connections" });

function listConnections() { return store.get("connections", []); }
function getConnection(connectionId) { return listConnections().find((c) => c.connectionId === connectionId) || null; }

function upsertConnection(conn) {
  const existing = listConnections().filter((c) => c.connectionId !== conn.connectionId);
  store.set("connections", [conn, ...existing]);
}

function removeConnection(connectionId) {
  store.set("connections", listConnections().filter((c) => c.connectionId !== connectionId));
}

module.exports = { listConnections, getConnection, upsertConnection, removeConnection };
