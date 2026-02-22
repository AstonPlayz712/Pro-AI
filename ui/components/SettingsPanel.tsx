"use client";

import React, { useEffect, useState } from "react";

import type { EngineMode } from "../core/engineSelector";
import { selectEngine } from "../core/engineSelector";
import { useConnectivity } from "../hooks/useConnectivity";
import { ensureDefaultSettings, setSettings, type SettingsState } from "../storage/db";
import { enqueueSettingsSync } from "../sync/offlineSync";

export function SettingsPanel(): React.JSX.Element {
  const { state: conn } = useConnectivity();
  const [settings, setLocalSettings] = useState<SettingsState>({
    engineMode: "auto",
    cloudModel: "gpt-4o-mini",
    localModel: "phi3",
  });
  const [selectedEngine, setSelectedEngine] = useState<string>("-");

  useEffect(() => {
    void (async () => {
      const s = await ensureDefaultSettings();
      setLocalSettings(s);
    })();
  }, []);

  useEffect(() => {
    void (async () => {
      const sel = await selectEngine(settings.engineMode);
      setSelectedEngine(sel.engineId);
    })();
  }, [settings.engineMode]);

  const update = async (patch: Partial<SettingsState>) => {
    const next = { ...settings, ...patch };
    setLocalSettings(next);
    await setSettings(next);
    await enqueueSettingsSync();
  };

  return (
    <div className="vsc-settings">
      <div className="vsc-panel-title">Settings</div>
      <div className="vsc-panel-body">
        <div className="vsc-form-row">
          <label className="vsc-label">Engine mode</label>
          <select
            className="vsc-select"
            value={settings.engineMode}
            onChange={(e) => void update({ engineMode: e.target.value as EngineMode })}
          >
            <option value="auto">Auto</option>
            <option value="force-cloud">Force Cloud</option>
            <option value="force-local">Force Local</option>
          </select>
        </div>

        <div className="vsc-form-row">
          <label className="vsc-label">Cloud model</label>
          <input
            className="vsc-input"
            value={settings.cloudModel}
            onChange={(e) => void update({ cloudModel: e.target.value })}
            placeholder="Cloud model id"
          />
        </div>

        <div className="vsc-form-row">
          <label className="vsc-label">Local model</label>
          <input
            className="vsc-input"
            value={settings.localModel}
            onChange={(e) => void update({ localModel: e.target.value })}
            placeholder="Local model id"
          />
        </div>

        <hr className="vsc-hr" />

        <div className="vsc-kv">
          <div className="vsc-kv__row">
            <div className="vsc-kv__k">Current engine</div>
            <div className="vsc-kv__v">{selectedEngine}</div>
          </div>
          <div className="vsc-kv__row">
            <div className="vsc-kv__k">Type</div>
            <div className="vsc-kv__v">{conn?.type ?? "unknown"}</div>
          </div>
          <div className="vsc-kv__row">
            <div className="vsc-kv__k">Downlink</div>
            <div className="vsc-kv__v">{conn?.downlink ?? 0} Mbps</div>
          </div>
          <div className="vsc-kv__row">
            <div className="vsc-kv__k">RTT</div>
            <div className="vsc-kv__v">{conn?.rtt ?? 0} ms</div>
          </div>
          <div className="vsc-kv__row">
            <div className="vsc-kv__k">Effective</div>
            <div className="vsc-kv__v">{conn?.effectiveType ?? "unknown"}</div>
          </div>
          <div className="vsc-kv__row">
            <div className="vsc-kv__k">Cloud health</div>
            <div className="vsc-kv__v">{String(conn?.cloudHealthy ?? false)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
