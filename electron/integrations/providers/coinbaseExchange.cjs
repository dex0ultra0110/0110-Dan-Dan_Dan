const { fetch } = require("undici");
const crypto = require("crypto");
const API = "https://api.exchange.coinbase.com";

function sign({ apiSecret, timestamp, method, requestPath, body }) {
  const key = Buffer.from(apiSecret, "base64");
  const prehash = `${timestamp}${method.toUpperCase()}${requestPath}${body || ""}`;
  return crypto.createHmac("sha256", key).update(prehash).digest("base64");
}

async function cbRequest(secrets, method, requestPath) {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const body = "";
  const signature = sign({ apiSecret: secrets.apiSecret, timestamp, method, requestPath, body });

  const res = await fetch(`${API}${requestPath}`, {
    method,
    headers: {
      "CB-ACCESS-KEY": secrets.apiKey,
      "CB-ACCESS-SIGN": signature,
      "CB-ACCESS-TIMESTAMP": timestamp,
      "CB-ACCESS-PASSPHRASE": secrets.passphrase,
      "Content-Type": "application/json"
    }
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Coinbase Exchange ${res.status}: ${text || "Request failed"}`);
  }
  return res.json();
}

const coinbaseExchangeProvider = {
  id: "coinbase_exchange",
  name: "Coinbase Exchange",
  auth: {
    type: "apiKey",
    fields: [
      { key: "apiKey", label: "API Key", secret: true },
      { key: "apiSecret", label: "API Secret (base64)", secret: true },
      { key: "passphrase", label: "Passphrase", secret: true }
    ]
  },
  requiredSecrets: ["apiKey", "apiSecret", "passphrase"],
  async validate(secrets) {
    if (!secrets.apiKey || !secrets.apiSecret || !secrets.passphrase) throw new Error("Missing API credentials");
    await cbRequest(secrets, "GET", "/accounts"); // if this returns, keys are good
  },
  async syncHoldings(secrets, _config, connectionId) {
    const accounts = await cbRequest(secrets, "GET", "/accounts");
    return {
      asOf: Date.now(),
      providerId: "coinbase_exchange",
      connectionId,
      accounts: accounts
        .map((a) => ({
          venue: "Coinbase Exchange",
          accountId: a.id,
          currency: a.currency,
          total: Number(a.balance),
          available: Number(a.available),
          hold: Number(a.hold)
        }))
        .filter((x) => Number.isFinite(x.total))
    };
  }
};

module.exports = { coinbaseExchangeProvider };
