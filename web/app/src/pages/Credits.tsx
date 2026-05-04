import { apiAsset } from "../api";

export function Credits() {
  return (
    <main className="page-grid">
      <section className="panel wide">
        <h2>Credits</h2>
        <p>
          This temporary v1.0 webpage serves as a private demonstration and
          planning interface for the MKID-IFTS simulator.
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
          overview document. This private demonstration page is intended to make the
          simulator easier to inspect and discuss before a polished public release.
        </p>
      </section>
      <section className="panel wide">
        <h3>Use note</h3>
        <p>
          This v1.0 website is a planning and demonstration interface for the
          current simulator. It should not be interpreted as a fully calibrated
          observatory ETC until validated against measured instrument and site data.
        </p>
      </section>
    </main>
  );
}
