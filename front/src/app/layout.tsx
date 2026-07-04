import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Vigie Marchés — analyse des candidatures aux marchés publics",
  description:
    "Outil open source : score de risque explicable et traçable à partir de données ouvertes (DECP, BODACC, HATVP, sanctions). Hackathon Assemblée nationale 2026.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body className="flex min-h-screen flex-col bg-slate-50 font-sans text-slate-900 antialiased">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <Link href="/" className="flex items-baseline gap-3">
              <span className="text-xl font-bold tracking-tight text-blue-900">
                Vigie Marchés
              </span>
              <span className="hidden text-sm text-slate-500 sm:inline">
                transparence des candidatures aux marchés publics
              </span>
            </Link>
            <nav className="flex items-center gap-5 text-sm font-medium">
              <Link href="/" className="text-slate-600 hover:text-blue-900">
                Analyse
              </Link>
              <Link href="/methodologie" className="text-slate-600 hover:text-blue-900">
                Méthodologie
              </Link>
              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
                open source
              </span>
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</main>
        <footer className="border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-5xl px-6 py-4 text-xs leading-relaxed text-slate-500">
            Prototype open source — hackathon de l&apos;Assemblée nationale 2026. Données :
            DECP, BODACC, Recherche d&apos;entreprises, HATVP (via Tricoteuses), gels des avoirs
            (DG Trésor), sanctions UE, EDES, Banque mondiale.{" "}
            <strong>L&apos;outil signale et source ; la décision reste humaine.</strong>
          </div>
        </footer>
      </body>
    </html>
  );
}
