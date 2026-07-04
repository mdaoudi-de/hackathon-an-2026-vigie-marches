import { getBareme, getProvenance } from "@/lib/api";

export const metadata = { title: "Méthodologie — Vigie Marchés" };

// Rendu à la requête (jamais au build) : l'API n'a pas à être disponible pendant `next build`.
export const dynamic = "force-dynamic";

export default async function Methodologie() {
  let bareme, provenance;
  try {
    [bareme, provenance] = await Promise.all([getBareme(), getProvenance()]);
  } catch (e) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        API injoignable : {String(e)}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <section>
        <h1 className="text-2xl font-bold">Méthodologie du score</h1>
        <p className="mt-1 text-sm text-slate-500">
          Barème version {bareme.version} — public, versionné, reproductible.
        </p>
        <p className="mt-4 max-w-3xl leading-relaxed text-slate-700">{bareme.description}</p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-semibold text-slate-800">Points par gravité</h2>
          <table className="mt-3 w-full text-sm">
            <tbody>
              {Object.entries(bareme.points_gravite).map(([gravite, points]) => (
                <tr key={gravite} className="border-t border-slate-100">
                  <td className="py-2 capitalize">{gravite}</td>
                  <td className="py-2 text-right font-mono">
                    {gravite === "redhibitoire" ? `${points} pts + niveau ROUGE immédiat` : `${points} pts`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-slate-500">
            Plafond : {bareme.plafond_famille} pts par famille, {bareme.plafond_global} pts au
            total.
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-semibold text-slate-800">Niveaux</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {Object.entries(bareme.seuils_niveaux).map(([niveau, regle]) => (
              <li key={niveau} className="flex items-start gap-2">
                <span
                  className={`mt-0.5 h-3 w-3 shrink-0 rounded-full ${
                    niveau === "VERT"
                      ? "bg-emerald-600"
                      : niveau === "ORANGE"
                        ? "bg-amber-500"
                        : "bg-red-600"
                  }`}
                />
                <span>
                  <strong>{niveau}</strong> — {regle}
                </span>
              </li>
            ))}
          </ul>
          <h3 className="mt-4 font-semibold text-slate-800">Correspondances sanctions</h3>
          <ul className="mt-2 space-y-1 text-sm text-slate-600">
            {Object.entries(bareme.seuils_matching_sanctions).map(([cle, regle]) => (
              <li key={cle}>
                <span className="font-medium">{cle.replaceAll("_", " ")}</span> : {regle}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="font-semibold text-slate-800">Familles de signaux</h2>
        <ul className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          {Object.entries(bareme.familles).map(([id, libelle]) => (
            <li key={id} className="rounded-lg bg-slate-50 px-3 py-2">
              {libelle}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-bold">Provenance des données locales</h2>
        <p className="mt-1 text-sm text-slate-500">
          Chaque table de la base est tracée : source, volume, date de collecte, licence.
        </p>
        <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Table</th>
                <th className="px-4 py-3">Lignes</th>
                <th className="px-4 py-3">Collectée le</th>
                <th className="px-4 py-3">Licence</th>
                <th className="px-4 py-3">Source</th>
              </tr>
            </thead>
            <tbody>
              {provenance.map((ligne) => (
                <tr key={ligne.table_cible} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-mono text-xs">{ligne.table_cible}</td>
                  <td className="px-4 py-2 text-right font-mono text-xs">
                    {ligne.lignes.toLocaleString("fr-FR")}
                  </td>
                  <td className="px-4 py-2 text-xs">{ligne.collecte_le.slice(0, 16)}</td>
                  <td className="px-4 py-2 text-xs">{ligne.licence ?? "—"}</td>
                  <td className="px-4 py-2 text-xs">
                    {ligne.url ? (
                      <a
                        href={ligne.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-700 underline decoration-dotted"
                      >
                        {ligne.source} ↗
                      </a>
                    ) : (
                      ligne.source
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Les miroirs OpenSanctions sont sous licence CC-BY-NC 4.0 (usage non commercial) : un
          déploiement en production substituerait les sources primaires ou une licence dédiée.
        </p>
      </section>
    </div>
  );
}
