import { useEffect } from "react";
import { isSample } from "../mission/geo";
import type { Mission } from "../mission/state";
import type { SourceRecord } from "../mission/types";
import "./evidence.css";

const KIND: Record<string, string> = { rover_sample_site: "Perseverance sampling site" };
const kindLabel = (kind: string) => KIND[kind] ?? kind.replace(/_/g, " ");

function SourceCard({ source, highlight }: { source: SourceRecord; highlight: boolean }) {
  const rows: [string, string | null | undefined][] = [
    ["Mission", source.mission],
    ["Instrument", source.instrument],
    ["Published", "publicationDate" in source ? source.publicationDate ?? "date not published" : undefined],
    ["Acquired", "acquisitionDate" in source ? source.acquisitionDate ?? "date not published" : undefined],
    ["Resolution", source.resolution],
    ["Attribution", source.attribution],
  ];
  return (
    <article id={`source-${source.sourceId}`} className={`card ev-source${highlight ? " highlight" : ""}`}>
      <h4><a href={source.url} target="_blank" rel="noopener noreferrer">{source.title}</a></h4>
      <dl>
        {rows.map(([label, value]) => value && <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl>
      {source.limitations && <p className="ev-limit"><strong>Limitation.</strong> {source.limitations}</p>}
      <p className="mono caption">{source.sourceId}</p>
    </article>
  );
}

export function EvidencePanel({ m }: { m: Mission }) {
  const { bundle, highlight } = m.state;
  const stop = m.stop;

  useEffect(() => {
    if (!highlight) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.getElementById(`source-${highlight}`)?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "nearest" });
  }, [highlight]);

  if (!bundle) return null;
  const { manifest, sources, warnings } = bundle.region;
  const own = new Set(stop?.sourceIds ?? []);
  const ordered = [...sources.filter((s) => own.has(s.sourceId)), ...sources.filter((s) => !own.has(s.sourceId))];
  const unlisted = [...own].filter((id) => !sources.some((s) => s.sourceId === id));

  return (
    <section className="evidence" aria-label="Destination evidence">
      {isSample(bundle) && (
        <p className="banner banner-outdated" role="note">Development sample data — not Mars terrain or a scientific result.</p>
      )}

      {stop ? (
        <>
          <h2 className="panel-heading">{stop.name ?? stop.id}</h2>
          {stop.kind && <p className="caption">{kindLabel(stop.kind)}</p>}
          {stop.description && <p className="prose">{stop.description}</p>}

          {stop.scientificQuestion && (
            <>
              <h3 className="section-label">Excursion question <span className="tag tag-hyp">Hypothetical crew scenario</span></h3>
              <p className="prose">{stop.scientificQuestion}</p>
            </>
          )}

          {!!stop.samples?.length && (
            <>
              <h3 className="section-label">Samples — NASA's inventory</h3>
              <div className="ev-scroll">
                <table className="metrics ev-samples">
                  <thead><tr><th>No.</th><th>Name</th><th>Type</th><th>Rock type</th><th>Sealed</th><th>Sol</th></tr></thead>
                  <tbody>
                    {stop.samples.map((x) => (
                      <tr key={x.number}><td>{x.number}</td><td>{x.name}</td><td>{x.type}</td><td>{x.rockType ?? "—"}</td><td>{x.sealedDate}</td><td>{x.sol}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="caption">Rock type is a geological classification from NASA's sample inventory — an interpretation, not a terrain measurement or measured chemistry.</p>
            </>
          )}

          {(stop.locationProvenance || "locationUncertaintyM" in stop) && (
            <>
              <h3 className="section-label">Location and its limits</h3>
              {stop.locationProvenance && <p className="prose">{stop.locationProvenance}</p>}
              {"locationUncertaintyM" in stop && (
                <p className="caption">
                  {stop.locationUncertaintyM == null ? "No geodetic uncertainty is published." : `Published location uncertainty: ${stop.locationUncertaintyM} m.`}
                </p>
              )}
            </>
          )}
        </>
      ) : (
        <p className="caption">Choose a destination to see its evidence.</p>
      )}

      <h3 className="section-label">Terrain measurements</h3>
      <p className="prose">
        Slope is derived from elevation{manifest.slopeMethod ? `: ${manifest.slopeMethod}` : "."} Grid resolution is {manifest.cellSizeM} m per cell;
        pixel spacing is not measurement accuracy.
      </p>
      {manifest.maskMeaning && <p className="caption">Missing-data mask: {manifest.maskMeaning}</p>}

      <h3 className="section-label">Sources</h3>
      {ordered.map((s) => <SourceCard key={s.sourceId} source={s} highlight={highlight === s.sourceId} />)}
      {unlisted.map((id) => (
        <p key={id} id={`source-${id}`} className={`card mono${highlight === id ? " highlight" : ""}`}>{id} — no source record supplied</p>
      ))}

      {!!warnings.length && (
        <>
          <h3 className="section-label">What this model does not show</h3>
          <ul className="ev-warnings">{warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        </>
      )}
    </section>
  );
}
