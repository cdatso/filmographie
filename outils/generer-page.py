#!/usr/bin/env python
"""
generer-page.py -- BKL-FOR-003 (b)

Interpreteur declare : Python 3.12.10 (python.exe, sur le PATH).
Bibliotheque standard uniquement (argparse, base64, html, json, re, sys,
urllib, pathlib, datetime) -- aucune installation.

Lit la table Supabase "filmographie" par l'API REST, en GET seul, avec
pagination obligatoire (limit/offset, ordre serveur impose : id.asc),
puis ecrit un index.html autoportant (sans JavaScript, sans ressource
tierce) a la racine du depot.

Fail-closed : le script n'annonce que ce qu'il a mesure ; il sort en
code non nul des qu'un controle echoue, et n'ecrit jamais une page
partielle.
"""

import argparse
import base64
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

INTERPRETEUR_DECLARE = "Python 3.12.10 (python.exe, PATH)"

COLONNES_ATTENDUES = {
    "realisateur", "titre", "titre_original", "categorie", "muet",
    "nb", "duree_min", "annee", "annee_source", "genres_sc", "pays",
}

TAILLE_PAGE = 500

ENTETES_TABLEAU = ("Realisateur", "Titre", "Annee", "Genres", "Pays", "Categorie")


def lire_fichier_acces(chemin):
    texte = Path(chemin).read_text(encoding="utf-8")
    url = None
    cle = None
    for ligne in texte.splitlines():
        ligne = ligne.strip().strip('"').strip("'")
        if not ligne:
            continue
        if ligne.startswith("http://") or ligne.startswith("https://"):
            url = ligne.rstrip("/")
        elif re.match(r"^(sb_publishable_|sb_secret_|eyJ)", ligne):
            cle = ligne
    if not url or not cle:
        print("ERREUR: fichier d'acces illisible (URL ou cle absente)", file=sys.stderr)
        sys.exit(1)
    return url, cle


def controler_cle(cle):
    """Refuse toute cle qui ressemble a une cle secrete/service_role."""
    if cle.startswith("sb_secret_") or "service_role" in cle:
        print(
            "ERREUR: la cle fournie ressemble a une cle secrete/service_role"
            " -- refus (GET seul autorise, jamais service_role)",
            file=sys.stderr,
        )
        sys.exit(1)
    segments = cle.split(".")
    if len(segments) == 3:
        try:
            segment = segments[1] + "=" * (-len(segments[1]) % 4)
            charge = json.loads(base64.urlsafe_b64decode(segment))
            if charge.get("role") == "service_role":
                print(
                    "ERREUR: le JWT fourni porte le role service_role -- refus",
                    file=sys.stderr,
                )
                sys.exit(1)
        except Exception:
            pass  # heuristique seulement ; ne bloque pas si non decodable


def appeler_api(url, cle, params):
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    requete = urllib.request.Request(
        f"{url}/rest/v1/filmographie?{qs}",
        headers={
            "apikey": cle,
            "Authorization": f"Bearer {cle}",
            "Prefer": "count=exact",
        },
    )
    try:
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            corps = reponse.read()
            content_range = reponse.headers.get("Content-Range", "")
            return json.loads(corps), content_range
    except urllib.error.URLError as exc:
        print(f"ERREUR: appel API echoue: {exc}", file=sys.stderr)
        sys.exit(1)


def recuperer_toutes_les_lignes(url, cle, taille_page):
    lignes = []
    ids_vus = set()
    offset = 0
    nb_pages = 0
    total_annonce = None
    while True:
        params = {
            "select": "*",
            "order": "id.asc",
            "limit": taille_page,
            "offset": offset,
        }
        page, content_range = appeler_api(url, cle, params)
        nb_pages += 1
        if content_range and "/" in content_range:
            queue = content_range.rsplit("/", 1)[1]
            if queue != "*":
                total_annonce = int(queue)
        for ligne in page:
            if ligne["id"] in ids_vus:
                print(
                    f"ERREUR: id {ligne['id']} deja vu -- pagination "
                    "incoherente (ordre serveur absent ou instable)",
                    file=sys.stderr,
                )
                sys.exit(1)
            ids_vus.add(ligne["id"])
        lignes.extend(page)
        if len(page) < taille_page:
            break
        offset += taille_page
    if total_annonce is None:
        print(
            "ERREUR: le serveur n'a jamais renvoye de total (Content-Range) "
            "-- total inconnu, page NON ecrite",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(lignes) != total_annonce:
        print(
            f"ERREUR: {len(lignes)} lignes recuperees mais total annonce "
            f"{total_annonce} -- page NON ecrite (troncature suspectee)",
            file=sys.stderr,
        )
        sys.exit(1)
    return lignes, nb_pages, total_annonce


def controler_colonnes(lignes):
    if not lignes:
        print("ERREUR: table vide -- rien a generer", file=sys.stderr)
        sys.exit(1)
    colonnes = set(lignes[0].keys())
    manquantes = COLONNES_ATTENDUES - colonnes
    if manquantes:
        print(
            f"ERREUR: colonnes attendues absentes de l'API: {sorted(manquantes)}",
            file=sys.stderr,
        )
        sys.exit(1)


def cle_tri(ligne):
    realisateur = ligne.get("realisateur") or ""
    sans_realisateur = realisateur == ""
    annee = ligne.get("annee")
    annee_tri = annee if annee is not None else 999999
    titre = ligne.get("titre") or ""
    return (sans_realisateur, realisateur, annee_tri, titre)


def valeur_annee_affichee(ligne):
    if ligne.get("annee") is not None:
        return str(ligne["annee"])
    if ligne.get("annee_source"):
        return str(ligne["annee_source"])
    return ""


def construire_corps_tableau(lignes_triees):
    corps = []
    rupture_ecrite = False
    nb_lignes_donnees = 0
    for ligne in lignes_triees:
        sans_realisateur = not ligne.get("realisateur")
        if sans_realisateur and not rupture_ecrite:
            corps.append(
                '<tr class="rupture"><td colspan="6">'
                "Films sans réalisateur renseigné</td></tr>"
            )
            rupture_ecrite = True

        realisateur = html.escape(ligne.get("realisateur") or "")
        titre = html.escape(ligne.get("titre") or "")
        annee = html.escape(valeur_annee_affichee(ligne))
        genres = html.escape(ligne.get("genres_sc") or "")
        pays = html.escape(ligne.get("pays") or "")
        categorie = html.escape(ligne.get("categorie") or "")

        marques = []
        if ligne.get("muet"):
            marques.append("muet")
        if ligne.get("nb"):
            marques.append("nb")
        marques_html = ""
        if marques:
            marques_html = f' <span class="marque">({html.escape(" / ".join(marques))})</span>'

        corps.append(
            "<tr>"
            f"<td>{realisateur}</td>"
            f"<td>{titre}</td>"
            f"<td>{annee}</td>"
            f"<td>{genres}</td>"
            f"<td>{pays}</td>"
            f"<td>{categorie}{marques_html}</td>"
            "</tr>"
        )
        nb_lignes_donnees += 1
    return "\n      ".join(corps), nb_lignes_donnees


CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  background: #faf8f4;
  color: #1a1a1a;
  padding: 2rem 1.5rem 3rem;
}
header { max-width: 64rem; margin: 0 auto 1.5rem; }
.mark {
  font-size: 0.78rem;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: #7d6629;
  margin: 0 0 0.8rem;
}
h1 { font-size: clamp(1.7rem, 4vw, 2.4rem); font-weight: 400; margin: 0; }
main { max-width: 64rem; margin: 0 auto; }
.table-wrap {
  overflow-x: auto;
  border: 1px solid #b8993f;
  border-radius: 2px;
}
table { border-collapse: collapse; width: 100%; min-width: 46rem; }
caption {
  text-align: left;
  caption-side: top;
  padding: 0.9rem 1rem;
  font-size: 0.92rem;
  color: #555555;
  border-bottom: 1px solid #b8993f;
}
th, td { padding: 0.55rem 0.9rem; text-align: left; vertical-align: top; }
thead th {
  border-bottom: 1px solid #b8993f;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 0.02em;
}
tbody tr + tr { border-top: 1px solid #e4ddcb; }
tr.rupture td {
  font-style: italic;
  color: #555555;
  border-top: 2px solid #b8993f;
  padding-top: 0.8rem;
}
.marque { color: #555555; font-size: 0.85rem; }
footer {
  max-width: 64rem;
  margin: 2rem auto 0;
  font-family: system-ui, sans-serif;
  font-size: 0.75rem;
  color: #555555;
}
footer a { color: inherit; }
@media (prefers-color-scheme: dark) {
  body { background: #14140f; color: #f0ede6; }
  .mark { color: #b8993f; }
  caption { color: #b5b0a6; }
  tbody tr + tr { border-top: 1px solid #2a2a20; }
  tr.rupture td { color: #b5b0a6; }
  .marque { color: #b5b0a6; }
  footer { color: #b5b0a6; }
}
""".strip()


def construire_page(lignes, horodatage):
    lignes_triees = sorted(lignes, key=cle_tri)
    n = len(lignes_triees)
    corps_tableau, nb_lignes_donnees = construire_corps_tableau(lignes_triees)
    cartouche = html.escape(
        f"généré le {horodatage} depuis la table filmographie "
        f"— {n} entrées"
    )
    entetes_html = "\n      ".join(
        f'<th scope="col">{e}</th>' for e in ENTETES_TABLEAU
    )
    page_html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Filmographie</title>
  <style>
{CSS}
  </style>
</head>
<body>
  <header>
    <p class="mark">Christo Datso</p>
    <h1>Filmographie</h1>
  </header>
  <main>
    <div class="table-wrap">
      <table>
        <caption>{cartouche}</caption>
        <thead>
          <tr>
      {entetes_html}
          </tr>
        </thead>
        <tbody>
      {corps_tableau}
        </tbody>
      </table>
    </div>
  </main>
  <footer>
    <p><a href="/">cdatso.be</a> — prototype d'apprentissage, BKL-FOR-003</p>
  </footer>
</body>
</html>
"""
    return page_html, nb_lignes_donnees


def analyser_arguments():
    parseur = argparse.ArgumentParser(description="Genere index.html depuis la table Supabase filmographie (lecture seule).")
    parseur.add_argument("--url", help="URL du projet Supabase (https://xxx.supabase.co)")
    parseur.add_argument("--cle", help="Cle publique (publishable / anon) du projet")
    parseur.add_argument("--acces", help="Chemin d'un fichier hors depot contenant l'URL et la cle (une par ligne)")
    parseur.add_argument("--sortie", help="Chemin du index.html a ecrire (defaut : racine du depot)")
    parseur.add_argument("--taille-page", type=int, default=TAILLE_PAGE, help="Taille de page pour la pagination (defaut 500)")
    args = parseur.parse_args()
    if args.acces:
        args.url, args.cle = lire_fichier_acces(args.acces)
    if not args.url or not args.cle:
        parseur.error("fournir soit --acces <fichier>, soit --url et --cle")
    return args


def main():
    args = analyser_arguments()
    controler_cle(args.cle)

    lignes, nb_pages, total = recuperer_toutes_les_lignes(args.url, args.cle, args.taille_page)
    controler_colonnes(lignes)

    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    page_html, nb_lignes_donnees = construire_page(lignes, horodatage)

    if nb_lignes_donnees != total:
        print(
            f"ERREUR: {nb_lignes_donnees} lignes ecrites dans la page mais "
            f"total mesure {total} -- page NON ecrite",
            file=sys.stderr,
        )
        sys.exit(1)

    racine_depot = Path(__file__).resolve().parent.parent
    sortie = Path(args.sortie) if args.sortie else racine_depot / "index.html"
    sortie.write_text(page_html, encoding="utf-8", newline="\n")

    taille_octets = sortie.stat().st_size

    print("=== rapport generer-page.py (fail-closed) ===")
    print(f"interpreteur declare : {INTERPRETEUR_DECLARE}")
    print(f"url appelee (sans cle) : {args.url}/rest/v1/filmographie?select=*&order=id.asc&limit={args.taille_page}&offset=...")
    print(f"pages recuperees : {nb_pages}")
    print(f"total annonce par le serveur (Content-Range) : {total}")
    print(f"lignes recuperees et confrontees au total : {len(lignes)}")
    print("colonnes attendues (11) presentes : oui")
    print(f"lignes de corps ecrites dans la page (comptees a la construction) : {nb_lignes_donnees}")
    print(f"horodatage du cartouche : {horodatage}")
    print(f"fichier ecrit : {sortie}")
    print(f"taille du fichier ecrit (octets) : {taille_octets}")


if __name__ == "__main__":
    main()
