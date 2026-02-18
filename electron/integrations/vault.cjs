const { safeStorage } = require("electron");
const ElectronStore = require("electron-store");

const Store = ElectronStore.default || ElectronStore;
const store = new Store({ name: "dandadan-vault" });

function saveSecrets(connectionId, secrets) {
  if (!safeStorage.isEncryptionAvailable()) throw new Error("Encryption unavailable on this OS/user session");
  const enc = safeStorage.encryptString(JSON.stringify(secrets)).toString("base64");
  store.set(`secrets.${connectionId}`, enc);
}

function readSecrets(connectionId) {
  const enc = store.get(`secrets.${connectionId}`, null);
  if (!enc) throw new Error("Missing secrets");
  const json = safeStorage.decryptString(Buffer.from(enc, "base64"));
  return JSON.parse(json);
}

function deleteSecrets(connectionId) {
  store.delete(`secrets.${connectionId}`);
}

module.exports = { saveSecrets, readSecrets, deleteSecrets };
