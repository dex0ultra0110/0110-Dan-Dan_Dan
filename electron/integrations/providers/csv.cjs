const csvProvider = {
  id: "csv",
  name: "CSV Import",
  auth: { type: "none", fields: [] },
  requiredSecrets: [],
  async validate() {},
  async syncHoldings(_secrets, _config, connectionId) {
    return { asOf: Date.now(), providerId: "csv", connectionId, accounts: [] };
  }
};

module.exports = { csvProvider };
