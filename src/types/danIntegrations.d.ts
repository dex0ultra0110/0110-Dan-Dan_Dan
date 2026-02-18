export {};

declare global {
  interface Window {
    danIntegrations: {
      providers: () => Promise<Array<{ id: string; name: string; auth: { type: string; fields: Array<{ key: string; label: string; secret: boolean }> } }>>;
      connect: (payload: { providerId: string; secrets: Record<string, string>; config?: Record<string, any> }) => Promise<{ connectionId: string; providerId: string }>;
      list: () => Promise<Array<{ connectionId: string; providerId: string; createdAt: number; config?: Record<string, any> }>>;
      sync: (connectionId: string) => Promise<any>;
      disconnect: (connectionId: string) => Promise<{ ok: boolean }>;
    };
  }
}
