import { apiAsset } from "../api";

export function Credits() {
  return (
    <main className="page-grid">
      <section className="panel wide">
        <h2>Credits</h2>
        <p>
          This v1.1 webpage is a planning and demonstration interface for the
          MKID-IFTS simulator (package 0.2.0).
        </p>
      </section>
      <section className="panel">
        <h3>Project team</h3>
        <ul className="clean-list">
          <li>Shayaan Auqil — project implementation and web ETC interface.</li>
          <li>Dr. Laurie Rousseau-Nepton — principal investigator and supervisor.</li>
        </ul>
      </section>
      <section className="panel">
        <h3>Links</h3>
        <ul className="clean-list">
          <li>
            <a href="https://github.com/r-nepton/High-res-IFTS-Lab" target="_blank" rel="noreferrer">
              See GitHub repository
            </a>
          </li>
          <li>
            <a
              href={apiAsset("/project-materials/MKID_IFTS_Project_Overview_Latest.pdf")}
              target="_blank"
              rel="noreferrer"
            >
              Download project overview PDF
            </a>
          </li>
        </ul>
      </section>
      <section className="panel wide">
        <h3>References and project materials</h3>
        <p>
          Project background and technical context are summarized in the downloadable
          overview document.
        </p>
      </section>
      <section className="panel wide">
        <h3>Use note</h3>
        <p>
          This website is a planning and demonstration interface for the current
          simulator. Absolute SNR values should not be treated as observatory-calibrated
          until validated against measured instrument and site data.
        </p>
      </section>
    </main>
  );
}
