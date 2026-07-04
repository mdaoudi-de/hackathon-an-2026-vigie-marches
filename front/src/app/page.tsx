import Link from "next/link";
import { Recherche } from "@/components/Recherche";

const CAS_DEMO = [
  {
    id: "552032534",
    nom: "DANONE",
    attendu: "VERT",
    couleur: "border-emerald-200 bg-emerald-50 hover:bg-emerald-100",
    pastille: "bg-emerald-600",
    detail: "Entreprise saine — mais inscrite au registre HATVP des représentants d'intérêts",
  },
  {
    id: "75058171200015",
    nom: "NEOLEDGE",
    attendu: "VERT",
    couleur: "border-sky-200 bg-sky-50 hover:bg-sky-100",
    pastille: "bg-sky-600",
    detail: "74 marchés publics au compteur : le track-record DECP restitué en une requête",
  },
  {
    id: "827879610",
    nom: "DAVEO",
    attendu: "ROUGE",
    couleur: "border-red-200 bg-red-50 hover:bg-red-100",
    pastille: "bg-red-600",
    detail:
      "Encore « active » au répertoire… mais en liquidation judiciaire au BODACC : l'angle mort comblé",
  },
];

export default function Accueil() {
  return (
    <div className="flex flex-col gap-10">
      <section className="pt-6 text-center">
        <h1 className="mx-auto max-w-3xl text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Vérifier un candidat à un marché public,{" "}
          <span className="text-blue-900">en secondes, preuves à l&apos;appui</span>
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-slate-600">
          Vigie Marchés croise automatiquement les données ouvertes — DECP, BODACC, sanctions,
          HATVP — et produit un score de risque <strong>déterministe, explicable et sourcé</strong>.
          Aucune boîte noire : chaque signal est relié à sa source et à sa date de collecte.
        </p>
      </section>

      <section className="mx-auto w-full max-w-2xl">
        <Recherche />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Cas de démonstration (données réelles)
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          {CAS_DEMO.map((cas) => (
            <Link
              key={cas.id}
              href={`/analyse/${cas.id}`}
              className={`rounded-xl border p-4 transition ${cas.couleur}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold">{cas.nom}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-bold text-white ${cas.pastille}`}
                >
                  {cas.attendu}
                </span>
              </div>
              <p className="mt-2 text-sm leading-snug text-slate-600">{cas.detail}</p>
              <p className="mt-2 font-mono text-xs text-slate-400">{cas.id}</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="grid gap-4 rounded-xl border border-slate-200 bg-white p-6 sm:grid-cols-3">
        {[
          {
            titre: "Explicable",
            texte:
              "Barème public et versionné, aligné sur les interdictions de soumissionner (art. L2141 du Code de la commande publique).",
          },
          {
            titre: "Traçable",
            texte:
              "Chaque signal porte sa preuve : source, URL, date de collecte, licence. La table de provenance est consultable.",
          },
          {
            titre: "Prudent",
            texte:
              "Une correspondance sur une liste de sanctions est « à vérifier », jamais une condamnation : l'outil ne conclut pas à la place de l'acheteur.",
          },
        ].map((b) => (
          <div key={b.titre}>
            <h3 className="font-semibold text-blue-900">{b.titre}</h3>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">{b.texte}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
