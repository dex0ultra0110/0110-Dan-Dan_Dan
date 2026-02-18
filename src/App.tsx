import { DanConnectionsPanel } from "./components/DanConnectionsPanel";

export default function App() {
  return (
    <div className="danAppBg danScanline min-h-screen font-sans">
      <div className="relative z-10 px-4 py-6 lg:px-8">
        <div className="danPanelEnter">
          <DanConnectionsPanel />
        </div>
      </div>
    </div>
  );
}
