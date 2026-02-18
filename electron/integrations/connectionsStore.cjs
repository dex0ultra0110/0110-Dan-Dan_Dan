const Store = require("electron-store");
const store = new Store({ name: "dandadan-connections" });

function listConnections() {
  return store.get("connections", []);
}

function getConnection(connectionId) {
  return listConnections().find((c) => c.connectionId === connectionId) || null;
}

function upsertConnection(conn) {
  const existing = listConnections().filter((c) => c.connectionId !== conn.connectionId);
  store.set("connections", [conn, ...existing]);
}

function removeConnection(connectionId) {
  const next = listConnections().filter((c) => c.connectionId !== connectionId);
  store.set("connections", next);
}

module.exports = { listConnections, getConnection, upsertConnection, removeConnection };
