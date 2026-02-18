const ccxt = require("ccxt");

function makeCcxtProvider(exchangeId) {
  if (!ccxt.exchanges.includes(exchangeId)) throw new Error(`CCXT unsupported exchange: ${exchangeId}`);

  const id = `ccxt:${exchangeId}`;
  const name = `CCXT / ${exchangeId}`;

  function normalizeBalances(venue, balanceObj) {
    const totals = balanceObj.total || {};
    const free = balanceObj.free || {};
    const used = balanceObj.used || {};

    return Object.keys(totals)
      .map((currency) => ({
        venue,
        currency,
        total: Number(totals[currency] || 0),
        available: Number(free[currency] || 0),
        hold: Number(used[currency] || 0)
      }))
      .filter((x) => x.total && Number.isFinite(x.total));
  }

  return {
    id,
    name,
    auth: {
      type: "apiKey",
      fields: [
        { key: "apiKey", label: "API Key", secret: true },
        { key: "apiSecret", label: "API Secret", secret: true },
        { key: "password", label: "Password (if required)", secret: true }
      ]
    },
    requiredSecrets: ["apiKey", "apiSecret"],
    async validate(secrets) {
      if (!secrets.apiKey || !secrets.apiSecret) throw new Error("Missing API key/secret");
      const ex = new ccxt[exchangeId]({
        apiKey: secrets.apiKey,
        secret: secrets.apiSecret,
        password: secrets.password || undefined,
        enableRateLimit: true
      });
      await ex.fetchBalance(); // if this returns, keys are good
      if (ex.close) await ex.close();
    },
    async syncHoldings(secrets, _config, connectionId) {
      const ex = new ccxt[exchangeId]({
        apiKey: secrets.apiKey,
        secret: secrets.apiSecret,
        password: secrets.password || undefined,
        enableRateLimit: true
      });
      const bal = await ex.fetchBalance();
      if (ex.close) await ex.close();

      return {
        asOf: Date.now(),
        providerId: id,
        connectionId,
        accounts: normalizeBalances(exchangeId, bal)
      };
    }
  };
}

module.exports = { makeCcxtProvider };
