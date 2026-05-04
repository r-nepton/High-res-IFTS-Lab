const sections = [
  [
    "Basic workflow",
    "A typical session starts with a source preset, then adjusts exposure time, scan geometry, observing conditions, MKID energy resolution, and order-sorting strategy. After pressing Compute ETC, first inspect the summary cards, then read the SNR plot, then use the rate and strategy plots to understand why the result changed."
  ],
  [
    "Choosing a source",
    "Start with a preset if you want a quick demonstration. The stellar preset behaves like a continuum source with an AB magnitude. The HII and planetary nebula presets emphasize emission lines. The faint-galaxy preset demonstrates an extended continuum-dominated case. These choices matter because line sources and continuum sources respond differently to order-sorting contamination."
  ],
  [
    "Exposure and scan controls",
    "Total exposure is the time budget used in the SNR calculation. n_steps is the number of interferometer samples. delta_x_m is the mirror-step spacing. Together they define how the Fourier transform samples the spectrum. Increasing steps or changing step size can improve resolution, but it also changes the folded-order layout and the exposure time per step."
  ],
  [
    "What n_steps means",
    "n_steps is the number of sampled interferometer positions. More steps generally provide more spectral information, but the web ETC divides the chosen total exposure across the scan. If total exposure is fixed, changing n_steps changes the exposure time per step."
  ],
  [
    "What delta_x_m means",
    "delta_x_m is the mirror-step spacing. It sets the Nyquist sampling scale and the free spectral range used for folding orders. Changing delta_x_m can make the scan more or less aggressive: it changes how much spectrum folds into each order and therefore changes the role of MKID order sorting."
  ],
  [
    "Observing conditions",
    "Airmass and water vapor affect transmission. Moon phase and thermal terms affect background. In an FTS, sky photons contribute noise across recovered channels, so the sky model is not just a visual background curve: it directly changes the SNR."
  ],
  [
    "MKID and order sorting choices",
    "R_E is the MKID energy resolving power. Higher R_E gives cleaner order assignment. Probabilistic assignment keeps all photons and weights them into possible orders. Hard-cut filtering rejects boundary photons using k_sigma. A larger k_sigma is more conservative, but discards more signal."
  ],
  [
    "What R_E does",
    "R_E is not the final spectral resolving power of the recovered FTS spectrum. It is the MKID photon-energy resolving power used to decide order membership. Low R_E means more uncertainty near order boundaries; high R_E makes order assignment cleaner."
  ],
  [
    "What k_sigma does",
    "k_sigma only matters for hard-cut filtering. It defines how wide the rejection zone is near an order boundary in units of the MKID energy uncertainty. Larger values are more conservative: fewer contaminated photons pass, but more signal is thrown away."
  ],
  [
    "Compute ETC",
    "Compute ETC is the main button. It runs the selected source and configuration through the analytical simulator. The output includes SNR versus wavelength, source/sky/total detector-entering rates, and a strategy ratio comparing probabilistic assignment to hard-cut filtering."
  ],
  [
    "Reading the plots",
    "The SNR plot shows which wavelengths are predicted to be easiest or hardest to observe. The rates plot explains whether the source, sky, or total detector rate is driving the result. The strategy-ratio plot is above 1 when probabilistic weighting gives higher SNR than hard-cut filtering, and below 1 when hard-cut filtering is favored."
  ],
  [
    "Reading the summary cards",
    "Max SNR reports the highest predicted SNR in the plotted wavelength range. Saturation reports whether the detector model raised a brightness warning. Strategy records the selected default order-sorting method, while the strategy-ratio plot still compares both methods."
  ],
  [
    "Target SNR solver",
    "The target-SNR solver answers the planning question in reverse. Instead of asking what SNR a fixed exposure gives, it asks how much exposure time is needed to reach a chosen SNR at a reference wavelength."
  ],
  [
    "Configuration search",
    "The optimizer checks a small built-in grid of scan choices and returns a recommended configuration. It is useful for exploration, but it is not an exhaustive instrument-design optimizer."
  ],
  [
    "What not to overinterpret",
    "The ETC is strongest for comparing trends and choices within the current model. Absolute predictions still depend on calibration of throughput, sky brightness, MKID energy resolution, and detector count-rate behavior."
  ],
  [
    "Export JSON",
    "Export stores the current computed arrays and metadata so results can be reused in notes, reports, or later comparison scripts."
  ]
];

export function Explore() {
  return (
    <main className="page-grid">
      <section className="tutorial-intro">
        <h2>How It Works</h2>
        <p>
          Use this page as a practical tutorial for the ETC tab. The web tool is
          organized around a simple workflow: choose a source, choose observing
          and instrument settings, compute the result, and interpret the plots.
          The calculation uses the analytical SNR model so that parameter changes
          are fast enough for interactive use.
        </p>
        <p>
          The goal is not only to get a number. The goal is to see which physical
          assumption is controlling the number: source brightness, sky background,
          scan geometry, detector energy resolution, or order-sorting strategy.
        </p>
      </section>
      <section className="stage-grid wide">
        {sections.map(([title, body]) => (
          <article className="panel" key={title}>
            <h3>{title}</h3>
            <p>{body}</p>
          </article>
        ))}
      </section>
      <section className="panel">
        <h3>Current assumptions</h3>
        <ul className="clean-list">
          <li>v1.0 emphasizes the analytical SNR path for speed and interactivity.</li>
          <li>The sky model includes representative OH structure and thermal continuum approximations.</li>
          <li>The public controls are capped to keep responses bounded and avoid expensive full simulations.</li>
          <li>Outputs are planning estimates until tied to measured throughput, sky, and detector calibration.</li>
        </ul>
      </section>
      <section className="panel">
        <h3>Potential v1.1 additions</h3>
        <ul className="clean-list">
          <li>Add a more formal SITELLE SN3 side-by-side benchmark table.</li>
          <li>Replace generic MKID energy-resolution scaling with measured calibration curves.</li>
          <li>Replace simplified sky and throughput terms with site/instrument-calibrated inputs.</li>
          <li>Add controlled file upload for user spectra after validation and storage limits are defined.</li>
        </ul>
      </section>
    </main>
  );
}
