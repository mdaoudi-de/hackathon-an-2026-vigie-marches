"use client";

/**
 * Génération du rapport d'aide à la décision (rédigé par Claude côté API).
 * Le score est déjà figé par le moteur : l'IA ne fait que la mise en forme sourcée.
 */

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { API_URL } from "@/lib/api";

interface RapportReponse {
  markdown: string;
  modele: string;
  genere_le: string;
}

export function Rapport({ identifiant }: { identifiant: string }) {
  const [rapport, setRapport] = useState<RapportReponse | null>(null);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  const generer = async () => {
    setChargement(true);
    setErreur(null);
    try {
      const reponse = await fetch(`${API_URL}/api/analyses/${identifiant}/rapport`);
      if (!reponse.ok) {
        const corps = await reponse.json().catch(() => null);
        throw new Error(corps?.detail ?? `Erreur API ${reponse.status}`);
      }
      setRapport(await reponse.json());
    } catch (e) {
      setErreur(String(e instanceof Error ? e.message : e));
    } finally {
      setChargement(false);
    }
  };

  const telecharger = () => {
    if (!rapport) return;
    const blob = new Blob([rapport.markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const lien = document.createElement("a");
    lien.href = url;
    lien.download = `rapport-${identifiant}.md`;
    lien.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-slate-800">Rapport d&apos;aide à la décision</h2>
          <p className="text-xs text-slate-500">
            Rédigé par Claude à partir des seuls signaux calculés — le score n&apos;est jamais
            modifié par l&apos;IA, chaque fait est sourcé.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={generer}
            disabled={chargement}
            className="rounded-lg bg-blue-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:opacity-50"
          >
            {chargement ? "Rédaction en cours…" : rapport ? "Régénérer" : "Générer le rapport"}
          </button>
          {rapport && (
            <button
              onClick={telecharger}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Télécharger (.md)
            </button>
          )}
        </div>
      </div>

      {chargement && (
        <p className="mt-4 text-sm text-slate-500">
          Claude rédige la note à partir du JSON de l&apos;analyse (10-30 s)…
        </p>
      )}
      {erreur && (
        <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {erreur}
        </p>
      )}
      {rapport && (
        <article className="prose prose-sm prose-slate mt-5 max-w-none border-t border-slate-100 pt-5">
          <ReactMarkdown>{rapport.markdown}</ReactMarkdown>
          <p className="text-xs text-slate-400">
            Généré le {rapport.genere_le.slice(0, 19).replace("T", " à ")} — modèle{" "}
            {rapport.modele}.
          </p>
        </article>
      )}
    </section>
  );
}
