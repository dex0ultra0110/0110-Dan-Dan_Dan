const { coinbaseExchangeProvider } = require("./coinbaseExchange.cjs");
const { csvProvider } = require("./csv.cjs");
const { makeCcxtProvider } = require("./ccxtFactory.cjs");
const ccxt = require("ccxt");

const NATIVE = {
  coinbase_exchange: coinbaseExchangeProvider,
  csv: csvProvider
};

const CCXT_CURATED = ["kraken", "binance", "kucoin", "bybit", "okx", "bitfinex", "gemini"];

function getProvider(providerId) {
  if (providerId.startsWith("ccxt:")) return makeCcxtProvider(providerId.slice("ccxt:".length));
  const p = NATIVE[providerId];
  if (!p) throw new Error(`Unknown provider: ${providerId}`);
  return p;
}

function listProviders() {
  const native = Object.values(NATIVE).map((p) => ({ id: p.id, name: p.name, auth: p.auth }));

  const ccxtExpanded = CCXT_CURATED
    .filter((id) => ccxt.exchanges.includes(id))
    .map((exId) => {
      const p = makeCcxtProvider(exId);
      return { id: p.id, name: p.name, auth: p.auth };
    });

  return [...native, ...ccxtExpanded];
}

module.exports = { getProvider, listProviders };
