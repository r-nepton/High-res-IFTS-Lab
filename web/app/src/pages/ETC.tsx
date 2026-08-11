import { useEffect, useMemo, useState } from "react";
import {
  compareStrategies,
  getPresets,
  optimizeConfig,
  runRates,
  runSnr,
  runTimeFromSnr,
  waitForApi
} from "../api";
import { ChartPanel } from "../components/ChartPanel";
import { NumberField } from "../components/NumberField";
import { SummaryCard } from "../components/SummaryCard";
import type { InstrumentPayload, Preset, RatesResponse, SnrResponse, SourcePayload, StrategyResponse } from "../types";

const defaultSource: SourcePayload = {
  mode: "point",
  spectral_type: "stellar_g2v",
  magnitude: 20,
  band: "r"
};

const defaultConfig: InstrumentPayload = {
  n_steps: 512,
  delta_x_m: 2e-6,
  n_sigma: 2048,
  airmass: 1.2,
  moon_phase: "new",
  pwv_mm: 2.5,
  ambient_temp_k: 273,
  thermal_emissivity: 0.08,
  D_primary: 3.6,
  mirror_coating: "silver",
  n_reflections: 3,
  optical_transmission: 0.88,
  n_pixels: 1,
  R_energy_ref: 40,
  R_energy_ref_nm: 500,
  R_energy_scaling: "sqrt",
  qe_model: "baseline",
  strategy: "probabilistic",
  k_sigma: 2,
  apodization: "hanning",
  phase_method: "mertz"
};

function zipSeries(x: number[], values: Record<string, number[]>) {
  return x.map((wavelength_nm, index) => {
    const row: Record<string, number> = { wavelength_nm };
    Object.entries(values).forEach(([key, series]) => {
      row[key] = series[index] ?? 0;
    });
    return row;
  });
}

function downloadJson(name: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

export function ETC() {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [source, setSource] = useState<SourcePayload>(defaultSource);
  const [config, setConfig] = useState<InstrumentPayload>(defaultConfig);
  const [tTotal, setTTotal] = useState(1024);
  const [targetSnr, setTargetSnr] = useState(10);
  const [refNm, setRefNm] = useState(656.3);
  const [snr, setSnr] = useState<SnrResponse | null>(null);
  const [rates, setRates] = useState<RatesResponse | null>(null);
  const [strategies, setStrategies] = useState<StrategyResponse | null>(null);
  const [requiredTime, setRequiredTime] = useState<number | null>(null);
  const [optimized, setOptimized] = useState<Record<string, number | string | boolean> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [apiReady, setApiReady] = useState(false);
  const [apiStatus, setApiStatus] = useState("Starting calculator…");

  async function wakeApi() {
    setApiReady(false);
    setApiStatus("Starting calculator…");
    setError(null);
    const ok = await waitForApi();
    if (ok) {
      setApiReady(true);
      setApiStatus("Calculator ready.");
      try {
        setPresets(await getPresets());
      } catch (err) {
        setError(String(err));
      }
      return;
    }
    setApiStatus("Calculator unavailable.");
    setError("Could not reach the API. Wait a moment and press Retry (free hosts may take up to a minute to wake).");
  }

  useEffect(() => {
    void wakeApi();
  }, []);

  const snrData = useMemo(() => {
    if (!snr) return [];
    return zipSeries(snr.snr.wavelength_nm, { snr: snr.snr.snr ?? [] });
  }, [snr]);

  const rateData = useMemo(() => {
    if (!rates) return [];
    return zipSeries(rates.rates.wavelength_nm, {
      source: rates.rates.source_rate_per_nm ?? [],
      sky: rates.rates.sky_rate_per_nm ?? [],
      total: rates.rates.total_rate_per_nm ?? []
    });
  }, [rates]);

  const strategyData = useMemo(() => {
    if (!strategies) return [];
    return zipSeries(strategies.ratio_prob_over_hard.wavelength_nm, {
      ratio: strategies.ratio_prob_over_hard.ratio ?? []
    });
  }, [strategies]);

  async function runAll() {
    setBusy(true);
    setError(null);
    try {
      const payload = { source, config, t_total_s: tTotal };
      const [snrOut, ratesOut, strategyOut] = await Promise.all([
        runSnr(payload),
        runRates({ source, config }),
        compareStrategies(payload)
      ]);
      setSnr(snrOut);
      setRates(ratesOut);
      setStrategies(strategyOut);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function solveTime() {
    setBusy(true);
    setError(null);
    try {
      const out = await runTimeFromSnr({ source, config, target_snr: targetSnr, ref_nm: refNm });
      setRequiredTime(out.t_total_s);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function optimize() {
    setBusy(true);
    setError(null);
    try {
      const out = await optimizeConfig({
        source,
        config,
        science_goal: { ref_nm: refNm, target_snr: targetSnr, target_resolution: 3000, max_time_s: tTotal }
      });
      setOptimized(out.config_recommended);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function applyPreset(id: string) {
    const preset = presets.find((item) => item.id === id);
    if (!preset) return;
    setSource({ ...defaultSource, ...preset.source });
    setConfig({ ...defaultConfig, ...preset.config });
  }

  return (
    <main className="etc-layout">
      <aside className="panel controls">
        <h2>ETC controls</h2>
        <div className={`api-status ${apiReady ? "ready" : "warming"}`}>
          <span>{apiStatus}</span>
          {!apiReady ? (
            <button type="button" onClick={() => void wakeApi()} disabled={apiStatus === "Starting calculator…"}>
              Retry
            </button>
          ) : null}
        </div>
        <label className="field">
          <span>Science preset</span>
          <select onChange={(event) => applyPreset(event.target.value)} defaultValue="" disabled={!apiReady}>
            <option value="" disabled>
              Select a preset
            </option>
            {presets.map((preset) => (
              <option value={preset.id} key={preset.id}>
                {preset.label}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Source mode</span>
          <select value={source.mode} onChange={(event) => setSource({ ...source, mode: event.target.value as SourcePayload["mode"] })}>
            <option value="point">Point source</option>
            <option value="extended">Extended source</option>
          </select>
        </label>

        {source.mode === "point" ? (
          <>
            <label className="field">
              <span>Template</span>
              <select value={source.spectral_type} onChange={(event) => setSource({ ...source, spectral_type: event.target.value })}>
                <option value="stellar_g2v">Stellar G2V</option>
                <option value="stellar_a0v">Stellar A0V</option>
                <option value="stellar_m5v">Stellar M5V</option>
                <option value="hii_region">HII region</option>
                <option value="planetary_nebula">Planetary nebula</option>
              </select>
            </label>
            <NumberField label="Magnitude (AB)" value={source.magnitude ?? 20} step={0.1} onChange={(value) => setSource({ ...source, magnitude: value })} />
            <NumberField label="Line flux (for HII)" value={source.line_flux ?? 0.02} step={0.001} min={0} onChange={(value) => setSource({ ...source, line_flux: value })} />
          </>
        ) : (
          <>
            <label className="field">
              <span>Template</span>
              <select value={source.template} onChange={(event) => setSource({ ...source, template: event.target.value })}>
                <option value="composite_galaxy">Composite galaxy</option>
                <option value="stellar_g2v">Stellar G2V</option>
              </select>
            </label>
            <NumberField label="Surface brightness" value={source.surface_brightness ?? 21} step={0.1} onChange={(value) => setSource({ ...source, surface_brightness: value })} />
          </>
        )}

        <NumberField label="Total exposure (s)" value={tTotal} step={10} min={1} onChange={setTTotal} />
        <NumberField label="Steps" value={config.n_steps ?? 512} step={16} min={16} onChange={(value) => setConfig({ ...config, n_steps: value })} />
        <NumberField label="Step size delta_x (m)" value={config.delta_x_m ?? 2e-6} step={1e-7} min={1e-8} onChange={(value) => setConfig({ ...config, delta_x_m: value })} />
        <NumberField label="R_E at reference" value={config.R_energy_ref ?? 40} step={1} min={1} onChange={(value) => setConfig({ ...config, R_energy_ref: value })} />
        <NumberField label="Airmass" value={config.airmass ?? 1.2} step={0.1} min={0} onChange={(value) => setConfig({ ...config, airmass: value })} />

        <label className="field">
          <span>Moon phase</span>
          <select value={config.moon_phase} onChange={(event) => setConfig({ ...config, moon_phase: event.target.value })}>
            <option value="new">New</option>
            <option value="crescent">Crescent</option>
            <option value="quarter">Quarter</option>
            <option value="full">Full</option>
          </select>
        </label>
        <label className="field">
          <span>Strategy</span>
          <select value={config.strategy} onChange={(event) => setConfig({ ...config, strategy: event.target.value as InstrumentPayload["strategy"] })}>
            <option value="probabilistic">Probabilistic</option>
            <option value="hard_cut">Hard-cut</option>
          </select>
        </label>
        <NumberField label="k_sigma" value={config.k_sigma ?? 2} step={0.25} min={0} onChange={(value) => setConfig({ ...config, k_sigma: value })} />

        <div className="button-row">
          <button type="button" onClick={runAll} disabled={busy || !apiReady}>
            {busy ? "Computing..." : "Compute ETC"}
          </button>
          <button type="button" onClick={() => snr && downloadJson("mkid-ifts-result.json", { snr, rates, strategies })}>
            Export JSON
          </button>
        </div>
      </aside>

      <section className="results">
        {error ? <div className="error-box">{error}</div> : null}
        <div className="summary-grid">
          <SummaryCard label="Max SNR" value={snr ? snr.stats.snr_max.toFixed(2) : "not run"} detail={snr ? `${snr.stats.snr_max_wavelength_nm.toFixed(1)} nm` : undefined} />
          <SummaryCard label="Total exposure" value={`${tTotal.toFixed(0)} s`} />
          <SummaryCard label="Saturation" value={snr?.snr.saturation_warning ? "warning" : "clear"} />
          <SummaryCard label="Strategy" value={config.strategy === "hard_cut" ? "Hard-cut" : "Probabilistic"} />
        </div>

        <ChartPanel title="SNR vs wavelength" data={snrData} series={[{ key: "snr", label: "SNR", color: "#7dd3fc" }]} yLabel="SNR per spectral channel" />
        <ChartPanel
          title="Detector-entering rates"
          data={rateData}
          series={[
            { key: "source", label: "Source", color: "#34d399" },
            { key: "sky", label: "Sky", color: "#fbbf24" },
            { key: "total", label: "Total", color: "#f472b6" }
          ]}
          yLabel="photons s^-1 nm^-1"
        />
        <ChartPanel title="Strategy ratio" data={strategyData} series={[{ key: "ratio", label: "SNR probabilistic / hard-cut", color: "#c084fc" }]} />

        <section className="panel tool-row">
          <div>
            <h3>Target SNR solver</h3>
            <div className="inline-fields">
              <NumberField label="Target SNR" value={targetSnr} step={1} min={0.1} onChange={setTargetSnr} />
              <NumberField label="Reference wavelength (nm)" value={refNm} step={0.1} min={100} onChange={setRefNm} />
              <button type="button" onClick={solveTime} disabled={busy || !apiReady}>
                Solve time
              </button>
            </div>
            {requiredTime ? <p>Required total time: {requiredTime.toFixed(1)} s</p> : null}
          </div>
          <div>
            <h3>Configuration search</h3>
            <button type="button" onClick={optimize} disabled={busy || !apiReady}>
              Optimize scan setup
            </button>
            {optimized ? <pre>{JSON.stringify(optimized, null, 2)}</pre> : null}
          </div>
        </section>

        <section className="panel assumption-box">
          <h3>Model assumptions</h3>
          <p>
            V1 uses the analytical ETC path for speed. It includes representative sky,
            atmosphere, telescope, MKID response, order sorting, and contamination-aware
            noise terms, but it is not a fully calibrated observatory ETC.
          </p>
        </section>
      </section>
    </main>
  );
}
