import { useEffect, useMemo, useState } from "react";

type Provider = {
  id: string;
  name: string;
  auth: { type: string; fields: Array<{ key: string; label: string; secret: boolean }> };
};

export function DanConnectionsPanel() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [providerId, setProviderId] = useState<string>("");
  const provider = useMemo(() => providers.find((p) => p.id === providerId) || null, [providers, providerId]);

  const [secrets, setSecrets] = useState<Record<string, string>>({});
  const [connections, setConnections] = useState<Array<{ connectionId: string; providerId: string; createdAt: number }>>(
    []
  );

  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string>("");
  const [lastSnapshot, setLastSnapshot] = useState<any>(null);

  async function refresh() {
    const [p, c] = await Promise.all([window.danIntegrations.providers(), window.danIntegrations.list()]);
    setProviders(p);
    setConnections(c);
    if (!providerId && p.length) setProviderId(p[0].id);
  }

  useEffect(() => {
    refresh().catch((e) => setStatus(String(e?.message || e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="danGlass rounded-lg p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-[12px] uppercase tracking-[0.1em] text-text-muted">DanDaDan</div>
          <h1 className="mt-2 text-[20px] font-semibold tracking-[-0.02em] text-text-primary">Integrations</h1>
        </div>
        <div className="text-[12px] uppercase tracking-[0.1em] text-text-muted">Keys stay local + encrypted</div>
      </div>

      <div className="mt-6 grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-5">
          <div className="text-[12px] uppercase tracking-[0.1em] text-text-muted">Provider</div>
          <select
            className="mt-2 danGlass w-full rounded-md px-4 py-3 min-h-12 text-[16px] text-text-primary outline-none"
            value={providerId}
            onChange={(e) => {
              setProviderId(e.target.value);
              setSecrets({});
              setStatus("");
            }}
          >
            {providers.map((p) => (
              <option key={p.id} value={p.id} style={{ background: "var(--bg-secondary)" }}>
                {p.name}
              </option>
            ))}
          </select>

          <div className="mt-6 text-[12px] uppercase tracking-[0.1em] text-text-muted">Saved Connections</div>
          <div className="mt-2 space-y-2">
            {connections.length === 0 ? (
              <div className="danGlass rounded-md px-4 py-3 min-h-12 text-[16px] text-text-muted">None yet.</div>
            ) : (
              connections.map((c) => (
                <div key={c.connectionId} className="danGlass rounded-md px-4 py-3 min-h-12">
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-[16px] font-semibold text-text-primary tabular-nums">{c.providerId}</span>
                    <div className="flex items-center gap-2">
                      <button
                        className="danGlass rounded-full px-4 py-3 min-h-12 text-[12px] uppercase tracking-[0.1em] text-text-muted hover:brightness-110 transition"
                        onClick={async () => {
                          setBusy(true);
                          setStatus("");
                          try {
                            const snap = await window.danIntegrations.sync(c.connectionId);
                            setLastSnapshot(snap);
                            setStatus("Sync OK");
                          } catch (e: any) {
                            setStatus(e?.message || String(e));
                          } finally {
                            setBusy(false);
                          }
                        }}
                      >
                        Sync
                      </button>
                      <button
                        className="danGlass rounded-full px-4 py-3 min-h-12 text-[12px] uppercase tracking-[0.1em] text-text-muted hover:brightness-110 transition"
                        onClick={async () => {
                          setBusy(true);
                          setStatus("");
                          try {
                            await window.danIntegrations.disconnect(c.connectionId);
                            setStatus("Disconnected");
                            await refresh();
                          } catch (e: any) {
                            setStatus(e?.message || String(e));
                          } finally {
                            setBusy(false);
                          }
                        }}
                      >
                        Drop
                      </button>
                    </div>
                  </div>
                  <div className="mt-2 text-[12px] uppercase tracking-[0.1em] text-text-muted break-all">
                    {c.connectionId}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-7">
          <div className="text-[12px] uppercase tracking-[0.1em] text-text-muted">Auth</div>
          <div className="mt-2 space-y-2">
            {!provider ? (
              <div className="danGlass rounded-md px-4 py-3 min-h-12 text-[16px] text-text-muted">Loading?</div>
            ) : provider.auth.fields.length === 0 ? (
              <div className="danGlass rounded-md px-4 py-3 min-h-12 text-[16px] text-text-muted">No keys required.</div>
            ) : (
              provider.auth.fields.map((f) => (
                <input
                  key={f.key}
                  className="danGlass w-full rounded-md px-4 py-3 min-h-12 text-[16px] text-text-primary placeholder:text-text-muted outline-none ring-1 ring-border-subtle focus:ring-1 focus:ring-accent-cyan transition"
                  type={f.secret ? "password" : "text"}
                  placeholder={f.label}
                  value={secrets[f.key] ?? ""}
                  onChange={(e) => setSecrets((s) => ({ ...s, [f.key]: e.target.value }))}
                  autoComplete="off"
                />
              ))
            )}

            <button
              className="danGlass rounded-full px-4 py-3 min-h-12 text-[12px] uppercase tracking-[0.1em] text-text-muted hover:brightness-110 transition disabled:opacity-60"
              disabled={busy || !provider}
              onClick={async () => {
                if (!provider) return;
                setBusy(true);
                setStatus("");
                try {
                  await window.danIntegrations.connect({ providerId: provider.id, secrets, config: {} });
                  setStatus("Keys valid. Saved.");
                  setSecrets({});
                  await refresh();
                } catch (e: any) {
                  setStatus(e?.message || String(e));
                } finally {
                  setBusy(false);
                }
              }}
            >
              Test & Save
            </button>

            {status ? <div className="danGlass rounded-md px-4 py-3 min-h-12 text-[16px] text-text-primary">{status}</div> : null}

            {lastSnapshot ? (
              <div className="mt-4 danGlass rounded-md px-4 py-3 min-h-12 text-[12px] text-text-muted whitespace-pre-wrap break-words">
                {JSON.stringify(lastSnapshot, null, 2)}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
