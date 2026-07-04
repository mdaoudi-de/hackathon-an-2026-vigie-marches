/**
 * Client typé de l'API Vigie Marchés.
 * Les types miroir du contrat JSON du moteur (vigie/modeles.py) — gelé au Run 2.
 */

export type Statut = "ok" | "declenche" | "a_verifier" | "indisponible";
export type Gravite = "info" | "mineur" | "majeur" | "redhibitoire";
export type Niveau = "VERT" | "ORANGE" | "ROUGE";

export interface Preuve {
  source: string;
  url: string;
  collecte_le: string;
  licence?: string | null;
  detail?: Record<string, unknown> | null;
}

export interface Signal {
  id: string;
  libelle: string;
  statut: Statut;
  valeur: string;
  gravite: Gravite;
  points: number;
  preuve: Preuve;
}

export interface Famille {
  id: string;
  libelle: string;
  points: number;
  plafond: number;
  signaux: Signal[];
}

export interface ScoreGlobal {
  niveau: Niveau;
  points: number;
  plafond: number;
  version_bareme: string;
  redhibitoire: boolean;
  nb_a_verifier: number;
}

export interface Candidat {
  siren: string;
  siret?: string | null;
  denomination?: string | null;
  etat_administratif?: string | null;
  preuve?: Preuve | null;
}

export interface Analyse {
  candidat: Candidat;
  score: ScoreGlobal;
  familles: Famille[];
  avertissements: string[];
  genere_le: string;
  duree_ms: number;
}

export interface CandidatResume {
  siren: string;
  denomination?: string | null;
  siret_siege?: string | null;
  etat_administratif?: string | null;
  activite_principale?: string | null;
  commune?: string | null;
}

export interface Bareme {
  version: string;
  description: string;
  points_gravite: Record<string, number>;
  plafond_famille: number;
  plafond_global: number;
  seuils_niveaux: Record<string, string>;
  seuils_matching_sanctions: Record<string, string>;
  familles: Record<string, string>;
}

export interface ProvenanceLigne {
  source: string;
  url: string;
  table_cible: string;
  lignes: number;
  collecte_le: string;
  licence?: string | null;
  note?: string | null;
}

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function getJson<T>(chemin: string): Promise<T> {
  const reponse = await fetch(`${API_URL}${chemin}`, { cache: "no-store" });
  if (!reponse.ok) {
    const corps = await reponse.text().catch(() => "");
    throw new Error(`API ${reponse.status} sur ${chemin} — ${corps.slice(0, 200)}`);
  }
  return reponse.json();
}

export const getAnalyse = (id: string) => getJson<Analyse>(`/api/analyses/${id}`);
export const getBareme = () => getJson<Bareme>(`/api/bareme`);
export const getProvenance = () => getJson<ProvenanceLigne[]>(`/api/provenance`);
export const chercherCandidats = (q: string) =>
  getJson<CandidatResume[]>(`/api/candidats?q=${encodeURIComponent(q)}`);
