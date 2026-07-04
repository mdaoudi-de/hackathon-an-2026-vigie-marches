"use client";

/** Champ de recherche avec autocomplétion sur /api/candidats. */

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { chercherCandidats, type CandidatResume } from "@/lib/api";

export function Recherche() {
  const router = useRouter();
  const [saisie, setSaisie] = useState("");
  const [resultats, setResultats] = useState<CandidatResume[]>([]);
  const [ouvert, setOuvert] = useState(false);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const minuteur = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (minuteur.current) clearTimeout(minuteur.current);
    const q = saisie.trim();
    if (q.length < 3) {
      setResultats([]);
      setOuvert(false);
      return;
    }
    minuteur.current = setTimeout(async () => {
      setChargement(true);
      setErreur(null);
      try {
        const trouves = await chercherCandidats(q);
        setResultats(trouves);
        setOuvert(true);
      } catch {
        setErreur("API injoignable — lancer `uvicorn api.main:app` puis réessayer.");
        setOuvert(false);
      } finally {
        setChargement(false);
      }
    }, 300);
    return () => {
      if (minuteur.current) clearTimeout(minuteur.current);
    };
  }, [saisie]);

  const analyser = (identifiant: string) => {
    setOuvert(false);
    router.push(`/analyse/${identifiant}`);
  };

  const chiffres = saisie.replace(/\D/g, "");
  const saisieDirecte = chiffres.length === 9 || chiffres.length === 14;

  return (
    <div className="relative">
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (saisieDirecte) analyser(chiffres);
          else if (resultats.length > 0) analyser(resultats[0].siren);
        }}
      >
        <input
          value={saisie}
          onChange={(e) => setSaisie(e.target.value)}
          onFocus={() => resultats.length && setOuvert(true)}
          placeholder="Nom d'entreprise, SIREN ou SIRET…"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-base shadow-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
          aria-label="Rechercher une entreprise"
        />
        <button
          type="submit"
          disabled={!saisieDirecte && resultats.length === 0}
          className="rounded-xl bg-blue-900 px-5 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {chargement ? "…" : "Analyser"}
        </button>
      </form>

      {erreur && <p className="mt-2 text-sm text-red-600">{erreur}</p>}

      {ouvert && resultats.length > 0 && (
        <ul className="absolute z-10 mt-2 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
          {resultats.map((r) => (
            <li key={r.siren}>
              <button
                type="button"
                onClick={() => analyser(r.siren)}
                className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left hover:bg-slate-50"
              >
                <span>
                  <span className="font-medium">{r.denomination}</span>
                  <span className="ml-2 text-xs text-slate-500">
                    {r.commune ?? ""}
                  </span>
                </span>
                <span className="flex items-center gap-2">
                  {r.etat_administratif !== "A" && (
                    <span className="rounded bg-red-50 px-1.5 py-0.5 text-xs font-semibold text-red-700">
                      cessée
                    </span>
                  )}
                  <span className="font-mono text-xs text-slate-400">{r.siren}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
