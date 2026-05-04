export function Home() {
  return (
    <main className="article-page">
      <article className="article-body">
        <p className="eyebrow">Principal investigator: Dr. Laurie Rousseau-Nepton</p>
        <h2>MKID-enabled imaging Fourier transform spectroscopy.</h2>
        <p>
          The High-Resolution IFTS Lab is developing a new class of astronomical
          instrument that pairs an Imaging Fourier Transform Spectrograph (IFTS)
          with energy-sensitive Microwave Kinetic Inductance Detectors (MKIDs).
          The concept addresses a central limitation of conventional imaging FTS
          systems: spectral folding that normally requires physical bandpass filters.
        </p>
        <p>
          An imaging FTS is attractive because it can produce spectra for every
          spatial element in a field, but the sampling rules are strict. The mirror
          scan determines spectral resolution, while the step size determines the
          bandwidth that can be sampled without aliasing. When high resolution is
          pursued with larger mirror steps, photons from outside the sampled band
          can fold into the same interferogram signal as the wavelengths of interest.
        </p>

        <h3>Instrument concept</h3>
        <p>
          A Michelson-based imaging FTS builds spectra by scanning optical path
          difference in discrete steps. The maximum path difference sets spectral
          resolution, while the step size sets the Nyquist-sampled bandwidth. At
          high resolution, out-of-band wavelengths can fold onto the measured band.
          Conventional systems such as SITELLE prevent this with filters, but each
          filter restricts the observation to a narrower wavelength interval.
        </p>
        <p>
          The MKID-IFTS concept moves the order-separation problem from the filter
          wheel into the detector and data-reduction pipeline. Instead of blocking
          most wavelengths before they enter the interferometer, the detector records
          an approximate photon energy. That energy information can then be used to
          decide which folding order a photon belongs to.
        </p>

        <h3>The MKID-IFTS approach</h3>
        <p>
          MKIDs record photon arrival time and photon energy. With resolving
          power on the order of R_E approximately 35-50, the detector energy tag
          can be used to assign photons to folding orders computationally. This
          makes filterless broadband operation possible in principle: the concept
          aims at 350-1100 nm coverage in a single interferogram scan, while
          retaining the wide-field character of imaging FTS observations.
        </p>
        <p>
          The approach is not simply a wider version of a filtered IFTS. Because
          photons are counted individually, order separation can be performed before
          or during reconstruction in a way that depends on the measured energy
          uncertainty. This introduces a new design trade: accepting some cross-order
          contamination may preserve more photons, while rejecting uncertain photons
          may reduce contamination but lower signal.
        </p>

        <figure className="inline-figure">
          <img src="/figures/00_pipeline_overview.png" alt="MKID-IFTS simulator pipeline" />
          <figcaption>
            <strong>Simulator signal chain.</strong> The web ETC uses the analytical
            branch of the same source-to-SNR pipeline: source, atmosphere, sky,
            telescope, IFTS optics, MKID response, order separation, recovery, and
            exposure-time calculation.
          </figcaption>
        </figure>

        <h3>Why the simulator was built</h3>
        <p>
          Before an MKID-IFTS instrument is built, its performance needs to be
          validated, its configuration space explored, and its likely science
          capability quantified. The simulator models the full signal chain from
          astrophysical source to recovered spectrum, including throughput, sky
          background, detector behavior, order sorting, and the SNR budget. The
          web ETC is the fast, interactive layer of that model: it lets a user
          change source, observing, detector, and scan assumptions and immediately
          see how the predicted SNR and strategy tradeoffs respond.
        </p>
        <p>
          The simulator has three layers. The full simulation generates folded-order
          interferograms and recovers spectra. The analytical SNR model provides a
          fast calculation of source, sky, contamination, and dark-noise terms. The
          ETC interface uses that fast analytical model to support interactive
          observation planning and configuration exploration.
        </p>

        <h3>Main research questions</h3>
        <p>
          The central questions are whether MKID energy resolution can replace
          physical filters, which reduction strategy produces lower noise, and
          how scan parameters should be chosen for different science cases. The
          two order-sorting strategies are deliberately different: hard-cut
          filtering rejects photons near order boundaries to reduce contamination,
          while probabilistic weighting retains photons but introduces correlated
          cross-order noise. The simulator compares those choices across source
          type, wavelength, energy resolution, sky background, and scan geometry.
        </p>
        <p>
          Red wavelengths are especially important because the 700-1100 nm region
          contains many bright OH airglow lines. In an FTS, photon noise from sky
          features can influence many recovered channels. The simulator makes it
          possible to test how MKID order sorting changes that background-limited
          regime, and whether the broadband filterless advantage remains useful for
          faint sources.
        </p>
      </article>
    </main>
  );
}
