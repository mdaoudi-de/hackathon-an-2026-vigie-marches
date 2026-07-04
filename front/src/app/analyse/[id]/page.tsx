import Link from "next/link";
import { Rapport } from "@/components/Rapport";
import { getAnalyse, type Gravite, type Niveau, type Signal } from "@/lib/api";

// Rendu à la requête (jamais au build) : l'API n'a pas à être disponible pendant `next build`.
export const dynamic = "force-dynamic";

const COULEURS_NIVEAU: Record<Niveau, { fond: string; texte: string; trait: string }> = {
  VERT: { fond: "bg-emerald-600", texte: "text-emerald-700", trait: "#059669" },
  ORANGE: { fond: "bg-amber-500", texte: "text-amber-700", trait: "#d97706" },
  ROUGE: { fond: "bg-red-600", texte: "text-red-700", trait: "#dc2626" },
};

function BadgeStatut({ signal }: { signal: Signal }) {
  if (signal.statut === "ok")
    return (
      <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">
        OK
      </span>
    );
  if (signal.statut === "a_verifier")
    return (
      <span className="rounded-full bg-violet-100 px-2 py-0.5 text-xs font-semibold text-violet-700">
        À VÉRIFIER
      </span>
    );
  if (signal.statut === "indisponible")
    return (
      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-500">
        INDISPONIBLE
      </span>
    );
  const parGravite: Record<Gravite, string> = {
    info: "bg-sky-50 text-sky-700",
    mineur: "bg-amber-100 text-amber-700",
    majeur: "bg-orange-100 text-orange-700",
    redhibitoire: "bg-red-100 text-red-700",
  };
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${parGravite[signal.gravite]}`}
    >
      {signal.gravite === "redhibitoire" ? "RÉDHIBITOIRE" : signal.gravite.toUpperCase()}
    </span>
  );
}

function Jauge({ points, plafond, niveau }: { points: number; plafond: number; niveau: Niveau }) {
  const part = Math.min(points / plafond, 1);
  const rayon = 40;
  const perimetre = 2 * Math.PI * rayon;
  return (
    <svg viewBox="0 0 100 100" className="h-28 w-28" role="img" aria-label={`${points} points sur ${plafond}`}>
      <circle cx="50" cy="50" r={rayon} fill="none" stroke="#e2e8f0" strokeWidth="10" />
      <circle
        cx="50"
        cy="50"
        r={rayon}
        fill="none"
        stroke={COULEURS_NIVEAU[niveau].trait}
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={`${part * perimetre} ${perimetre}`}
        transform="rotate(-90 50 50)"
      />
      <text x="50" y="47" textAnchor="middle" className="fill-slate-900 text-xl font-bold">
        {points}
      </text>
      <text x="50" y="64" textAnchor="middle" className="fill-slate-400 text-[10px]">
        / {plafond} pts
      </text>
    </svg>
  );
}

export default async function FicheAnalyse({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let analyse;
  try {
    analyse = await getAnalyse(id);
  } catch (e) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6">
        <h1 className="font-bold text-red-800">Analyse impossible</h1>
        <p className="mt-2 text-sm text-red-700">{String(e)}</p>
        <p className="mt-2 text-sm text-slate-600">
          Vérifier que l&apos;API est lancée (<code>uvicorn api.main:app</code>) et que
          l&apos;identifiant est un SIREN (9 chiffres) ou un SIRET (14 chiffres).
        </p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-blue-900">
          ← Retour à la recherche
        </Link>
      </div>
    );
  }

  const { candidat, score, familles, avertissements } = analyse;
  const couleurs = COULEURS_NIVEAU[score.niveau];

  return (
    <div className="flex flex-col gap-6">
      {/* Bandeau identité + score */}
      <section className="flex flex-col items-center gap-6 rounded-xl border border-slate-200 bg-white p-6 sm:flex-row">
        <Jauge points={score.points} plafond={score.plafond} niveau={score.niveau} />
        <div className="flex-1 text-center sm:text-left">
          <div className="flex flex-wrap items-center justify-center gap-3 sm:justify-start">
            <h1 className="text-2xl font-bold">{candidat.denomination ?? "Dénomination inconnue"}</h1>
            <span
              className={`rounded-full px-3 py-1 text-sm font-bold text-white ${couleurs.fond}`}
            >
              {score.niveau}
            </span>
          </div>
          <p className="mt-1 font-mono text-sm text-slate-500">
            SIREN {candidat.siren}
            {candidat.siret ? ` · SIRET ${candidat.siret}` : ""}
            {candidat.etat_administratif
              ? ` · état ${candidat.etat_administratif === "A" ? "actif" : "cessé"}`
              : ""}
          </p>
          {score.redhibitoire && (
            <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-800">
              ⚠ Signal rédhibitoire détecté : motif d&apos;interdiction de soumissionner
              (art. L2141 du Code de la commande publique). Vérification humaine requise.
            </p>
          )}
          {score.nb_a_verifier > 0 && !score.redhibitoire && (
            <p className="mt-3 text-sm font-medium text-violet-700">
              {score.nb_a_verifier} point(s) à vérifier manuellement.
            </p>
          )}
          <p className="mt-2 text-xs text-slate-400">
            Barème v{score.version_bareme} —{" "}
            <Link href="/methodologie" className="underline hover:text-blue-900">
              méthodologie publique
            </Link>
          </p>
        </div>
      </section>

      {avertissements.length > 0 && (
        <section className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <h2 className="mb-1 font-semibold">Limites sur ce dossier</h2>
          <ul className="list-inside list-disc space-y-1">
            {avertissements.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Familles de signaux */}
      <section className="flex flex-col gap-4">
        {familles.map((famille) => {
          const actif = famille.signaux.some((s) => s.statut !== "ok");
          return (
            <details
              key={famille.id}
              open={actif}
              className="group rounded-xl border border-slate-200 bg-white"
            >
              <summary className="flex cursor-pointer items-center justify-between px-5 py-4 font-semibold text-slate-800 [&::-webkit-details-marker]:hidden">
                <span>{famille.libelle}</span>
                <span className="flex items-center gap-3 text-sm">
                  <span
                    className={
                      famille.points > 0 ? "font-bold text-orange-700" : "text-slate-400"
                    }
                  >
                    {famille.points}/{famille.plafond} pts
                  </span>
                  <span className="text-slate-400 transition group-open:rotate-90">›</span>
                </span>
              </summary>
              <div className="divide-y divide-slate-100 border-t border-slate-100">
                {famille.signaux.map((signal) => (
                  <div key={signal.id} className="flex flex-col gap-1 px-5 py-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <BadgeStatut signal={signal} />
                      <span className="font-medium text-slate-800">{signal.libelle}</span>
                      {signal.points > 0 && signal.statut !== "ok" && (
                        <span className="ml-auto text-sm font-semibold text-orange-700">
                          +{signal.points} pts
                        </span>
                      )}
                    </div>
                    <p className="text-sm leading-relaxed text-slate-600">{signal.valeur}</p>
                    {signal.preuve.url && (
                      <a
                        href={signal.preuve.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-700 underline decoration-dotted hover:text-blue-900"
                      >
                        preuve : {signal.preuve.source} (collecté le{" "}
                        {signal.preuve.collecte_le.slice(0, 10)}) ↗
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </details>
          );
        })}
      </section>

      <Rapport identifiant={candidat.siret ?? candidat.siren} />

      <p className="text-center text-xs text-slate-400">
        Analyse générée le {analyse.genere_le.replace("T", " à ").slice(0, 19)} en{" "}
        {analyse.duree_ms} ms. Score déterministe (aucune IA dans le calcul) — chaque signal est
        sourcé et datable. Ce rapport est une aide à la décision, pas une décision.
      </p>
    </div>
  );
}
