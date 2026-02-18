const crypto = require("crypto");
const { z } = require("zod");
const { getProvider, listProviders } = require("./providers/registry.cjs");
const { saveSecrets, readSecrets, deleteSecrets } = require("./vault.cjs");
const { listConnections, getConnection, upsertConnection, removeConnection } = require("./connectionsStore.cjs");

const connectSchema = z.object({
  providerId: z.string(),
  secrets: z.record(z.string(), z.string()),
  config: z.record(z.any()).optional()
});

async function connectIntegration(payload) {
  const { providerId, secrets, config } = connectSchema.parse(payload);
  const provider = getProvider(providerId);

  await provider.validate(secrets, config || {});

  const connectionId = `${providerId}::${crypto.randomUUID()}`;
  saveSecrets(connectionId, secrets);

  upsertConnection({ connectionId, providerId, createdAt: Date.now(), config: config || {} });
  return { connectionId, providerId };
}

async function syncIntegration(connectionId) {
  const conn = getConnection(connectionId);
  if (!conn) throw new Error("Unknown connectionId");

  const provider = getProvider(conn.providerId);
  const secrets = readSecrets(connectionId);

  return provider.syncHoldings(secrets, conn.config || {}, connectionId);
}

async function disconnectIntegration(connectionId) {
  const conn = getConnection(connectionId);
  if (!conn) throw new Error("Unknown connectionId");

  deleteSecrets(connectionId);
  removeConnection(connectionId);

  return { ok: true };
}

module.exports = { connectIntegration, syncIntegration, disconnectIntegration, listConnections, listProviders };
