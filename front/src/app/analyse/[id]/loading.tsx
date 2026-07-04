export default function ChargementAnalyse() {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-900" />
      <p className="font-medium text-slate-700">Interrogation des sources publiques…</p>
      <p className="max-w-md text-sm text-slate-500">
        Recherche d&apos;entreprises, BODACC, listes de sanctions, DECP (3,1 M de marchés),
        répertoire HATVP — chaque signal sera accompagné de sa preuve.
      </p>
    </div>
  );
}
