#!/usr/bin/env python
# -*- coding: ascii -*-
#
# preparer-filmographie.py
# Convertit l'export CP1252 de la filmographie source vers un CSV
# RFC4180 UTF-8 sans BOM, pret pour import Supabase.
#
# Interpreter d'execution declare : Python 3.12.10 (python.exe sur le PATH,
# AppData\Local\Programs\Python\Python312\python.exe). Bibliotheque
# standard uniquement (csv, hashlib, re, sys, argparse, pathlib).
#
# Script fail-closed : il n'annonce que ce qu'il a mesure, et sort en
# code non nul si un seul controle echoue. Aucune installation requise.

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
CLAUDE_DIR = REPO_DIR.parent.parent

DEFAULT_SOURCE = CLAUDE_DIR / "CIN" / "bibliotheque" / "Filmographie" / "films-db-log-simplified-4-supabase-test.csv"
DEFAULT_OUTPUT = REPO_DIR / "donnees" / "filmographie-utf8.csv"

EXPECTED_SOURCE_SHA256 = "36357264EFDD1430A49E83CDDE4F70B0779A00F88F00F9DAF7ECD0A4BDCAE689"

EXPECTED_DATA_LINES = 1998
EXPECTED_OUTPUT_COLUMNS = 11

EXPECTED_CATEGORIE_FILM = 1693
EXPECTED_MUET_VRAI = 107
EXPECTED_NB_VRAI = 396
EXPECTED_ANNEE_VIDE = 18
EXPECTED_ANNEE_SOURCE_VIDE = 11
EXPECTED_DUREE_VIDE = 17

# "Terminator 2; Judgment Day" -- ASCII pur, aucune substitution requise.
EXPECTED_TRAP_802 = "Terminator 2; Judgment Day"
# 'Carnet de notes sur "Vetements et villes"' -- le e de Vetements porte un
# accent circonflexe dans la source ; construit par echappement unicode
# pour garder ce fichier source en ASCII pur (convention gate AH 16/07).
EXPECTED_TRAP_1935 = 'Carnet de notes sur "V' + chr(0x00EA) + 'tements et villes"'

OUTPUT_HEADER = [
    "realisateur", "titre", "titre_original", "categorie", "muet", "nb",
    "duree_min", "annee", "annee_source", "genres_sc", "pays",
]

ANNEE_DOUBLE_RE = re.compile(r"^\s*\d{4}\s*/\s*\d{4}\s*$")
ANNEE_ENTIER_RE = re.compile(r"^\d{4}$")
DUREE_ENTIER_RE = re.compile(r"^\d+$")

UTF8_E_ACUTE = b"\xc3\xa9"
UTF8_BOM = b"\xef\xbb\xbf"


class ControleEchoue(Exception):
    pass


def sha256_fichier(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            h.update(bloc)
    return h.hexdigest().upper()


def classer_annee(valeur_brute):
    valeur = valeur_brute.strip()
    if valeur == "":
        return None, ""
    if ANNEE_DOUBLE_RE.match(valeur_brute):
        return None, valeur_brute
    if ANNEE_ENTIER_RE.match(valeur):
        return int(valeur), valeur_brute
    raise ControleEchoue(
        "valeur 'annee' non reconnue (ni vide, ni AAAA, ni AAAA / AAAA) : "
        + repr(valeur_brute)
    )


def classer_duree(valeur_brute):
    valeur = valeur_brute.strip()
    if valeur == "":
        return ""
    if DUREE_ENTIER_RE.match(valeur):
        return str(int(valeur))
    raise ControleEchoue(
        "valeur 'duree (min.)' non numerique et non vide : " + repr(valeur_brute)
    )


def classer_booleen(valeur_brute, nom_colonne):
    valeur = valeur_brute.strip()
    if valeur == "Y":
        return "true"
    if valeur == "":
        return "false"
    raise ControleEchoue(
        "valeur inattendue dans la colonne '" + nom_colonne + "' : " + repr(valeur_brute)
    )


def lire_source(chemin_source):
    with open(chemin_source, "r", encoding="cp1252", newline="") as f:
        lecteur = csv.reader(f, delimiter=";")
        entete = next(lecteur)
        lignes = list(lecteur)
    return entete, lignes


def verifier_entete(entete):
    if len(entete) != 12:
        raise ControleEchoue(
            "entete source : 12 champs attendus, " + str(len(entete)) + " lus"
        )
    if entete[1].strip() != "TITRES":
        raise ControleEchoue("entete source : colonne 2 attendue 'TITRES', lue " + repr(entete[1]))
    if entete[4].strip() != "Muet":
        raise ControleEchoue("entete source : colonne 5 attendue 'Muet', lue " + repr(entete[4]))
    if entete[5].strip() != "N/B":
        raise ControleEchoue("entete source : colonne 6 attendue 'N/B', lue " + repr(entete[5]))
    if entete[10].strip() != "" or entete[11].strip() != "":
        raise ControleEchoue("entete source : les 2 colonnes terminales devraient etre vides")


def convertir_ligne(ligne, numero):
    if len(ligne) != 12:
        raise ControleEchoue(
            "ligne " + str(numero) + " : 12 champs attendus, " + str(len(ligne)) + " lus"
        )
    realisateur = ligne[0]
    titre = ligne[1]
    titre_original = ligne[2]
    categorie = ligne[3]
    muet = classer_booleen(ligne[4], "Muet")
    nb = classer_booleen(ligne[5], "N/B")
    duree_min = classer_duree(ligne[6])
    annee, annee_source = classer_annee(ligne[7])
    genres_sc = ligne[8]
    pays = ligne[9]
    return [
        realisateur, titre, titre_original, categorie, muet, nb,
        duree_min, "" if annee is None else str(annee), annee_source,
        genres_sc, pays,
    ]


def ecrire_sortie(chemin_sortie, entete, lignes_sortie):
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin_sortie, "w", encoding="utf-8", newline="") as f:
        ecrivain = csv.writer(f, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        ecrivain.writerow(entete)
        for ligne in lignes_sortie:
            ecrivain.writerow(ligne)
            f.flush()


def relire_et_controler(chemin_sortie, lignes_attendues):
    rapport = {}

    with open(chemin_sortie, "rb") as f:
        premiers_octets = f.read(3)
    if premiers_octets == UTF8_BOM:
        raise ControleEchoue("controle 3 : BOM UTF-8 present en tete de fichier (interdit sur ce fichier)")

    with open(chemin_sortie, "r", encoding="utf-8", newline="") as f:
        lecteur = csv.reader(f)
        entete_relue = next(lecteur)
        lignes_relues = list(lecteur)

    if entete_relue[0] != "realisateur":
        raise ControleEchoue("controle 3 : premiere colonne attendue 'realisateur', lue " + repr(entete_relue[0]))
    rapport["controle_3_entete"] = "OK : " + entete_relue[0]

    if len(lignes_relues) != lignes_attendues:
        raise ControleEchoue(
            "controle 1 : lignes ecrites relues = " + str(len(lignes_relues))
            + ", attendu " + str(lignes_attendues)
        )
    rapport["controle_1_lignes_ecrites"] = len(lignes_relues)

    if len(entete_relue) != EXPECTED_OUTPUT_COLUMNS:
        raise ControleEchoue(
            "controle 2 : " + str(len(entete_relue)) + " colonnes en sortie, attendu "
            + str(EXPECTED_OUTPUT_COLUMNS)
        )
    for i, ligne in enumerate(lignes_relues):
        if len(ligne) != EXPECTED_OUTPUT_COLUMNS:
            raise ControleEchoue(
                "controle 2 : ligne " + str(i + 2) + " a " + str(len(ligne)) + " colonnes"
            )
    rapport["controle_2_colonnes"] = EXPECTED_OUTPUT_COLUMNS

    with open(chemin_sortie, "rb") as f:
        contenu_brut = f.read()
    try:
        contenu_brut.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ControleEchoue("controle 4 : fichier de sortie n'est pas UTF-8 valide : " + str(exc))
    if UTF8_E_ACUTE not in contenu_brut:
        raise ControleEchoue("controle 4 : aucune sequence UTF-8 d'accent (C3 A9) trouvee en sortie")
    rapport["controle_4_accents_utf8"] = "OK : sequence C3 A9 presente, decodage UTF-8 strict reussi"

    lignes_802 = [l for l in lignes_relues if l[2] == EXPECTED_TRAP_802]
    if len(lignes_802) != 1:
        raise ControleEchoue(
            "controle 5 : " + str(len(lignes_802)) + " ligne(s) avec titre_original == "
            + repr(EXPECTED_TRAP_802) + ", attendu 1"
        )
    rapport["controle_5_piege_802"] = "OK : 1 occurrence"

    lignes_1935 = [l for l in lignes_relues if l[1] == EXPECTED_TRAP_1935]
    if len(lignes_1935) != 1:
        raise ControleEchoue(
            "controle 6 : " + str(len(lignes_1935)) + " ligne(s) avec titre == "
            + repr(EXPECTED_TRAP_1935) + ", attendu 1"
        )
    rapport["controle_6_piege_1935"] = "OK : 1 occurrence"

    idx = {nom: i for i, nom in enumerate(OUTPUT_HEADER)}
    n_categorie_film = sum(1 for l in lignes_relues if l[idx["categorie"]] == "Film")
    n_muet_vrai = sum(1 for l in lignes_relues if l[idx["muet"]] == "true")
    n_nb_vrai = sum(1 for l in lignes_relues if l[idx["nb"]] == "true")
    n_annee_vide = sum(1 for l in lignes_relues if l[idx["annee"]] == "")
    n_annee_source_vide = sum(1 for l in lignes_relues if l[idx["annee_source"]] == "")
    n_duree_vide = sum(1 for l in lignes_relues if l[idx["duree_min"]] == "")

    decomptes = {
        "categorie=Film": (n_categorie_film, EXPECTED_CATEGORIE_FILM),
        "muet=true": (n_muet_vrai, EXPECTED_MUET_VRAI),
        "nb=true": (n_nb_vrai, EXPECTED_NB_VRAI),
        "annee vide": (n_annee_vide, EXPECTED_ANNEE_VIDE),
        "annee_source vide": (n_annee_source_vide, EXPECTED_ANNEE_SOURCE_VIDE),
        "duree_min vide": (n_duree_vide, EXPECTED_DUREE_VIDE),
    }
    for nom, (mesure, attendu) in decomptes.items():
        if mesure != attendu:
            raise ControleEchoue(
                "controle 7 : " + nom + " mesure=" + str(mesure) + " attendu=" + str(attendu)
            )
    rapport["controle_7_decomptes"] = decomptes

    return rapport


def main():
    parser = argparse.ArgumentParser(description="Conversion filmographie CP1252 vers UTF-8 RFC4180")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--sortie", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    print("preparer-filmographie.py -- interpreter Python 3.12.10 (declare)")
    print("source  : " + str(args.source))
    print("sortie  : " + str(args.sortie))

    print("")
    print("etape 1/4 : controle SHA-256 de la source avant lecture")
    sha_avant = sha256_fichier(args.source)
    print("  SHA-256 mesure  : " + sha_avant)
    print("  SHA-256 attendu : " + EXPECTED_SOURCE_SHA256)
    if sha_avant != EXPECTED_SOURCE_SHA256:
        print("ECART : le fichier source a change depuis la mesure du mandat.")
        print("Le script s'arrete sans ecrire de sortie (fail-closed).")
        sys.exit(1)

    print("")
    print("etape 2/4 : lecture de la source (csv.reader, encoding=cp1252, delimiter=';')")
    entete_source, lignes_source = lire_source(args.source)
    verifier_entete(entete_source)
    n_lignes_lues = len(lignes_source)
    print("  lignes de donnees lues : " + str(n_lignes_lues))
    if n_lignes_lues != EXPECTED_DATA_LINES:
        print("ECART : " + str(n_lignes_lues) + " lignes lues, attendu " + str(EXPECTED_DATA_LINES))
        print("Le script s'arrete sans ecrire de sortie (fail-closed).")
        sys.exit(1)

    print("")
    print("etape 3/4 : conversion et ecriture au fil de l'eau vers " + str(args.sortie))
    try:
        lignes_converties = []
        for numero, ligne in enumerate(lignes_source, start=2):
            lignes_converties.append(convertir_ligne(ligne, numero))
        ecrire_sortie(args.sortie, OUTPUT_HEADER, lignes_converties)
    except ControleEchoue as exc:
        print("ECHEC DE CONVERSION : " + str(exc))
        sys.exit(1)
    print("  lignes ecrites : " + str(len(lignes_converties)))

    print("")
    print("etape 4/4 : relecture programmatique et controles numerotes 1 a 8")
    try:
        rapport = relire_et_controler(args.sortie, EXPECTED_DATA_LINES)
    except ControleEchoue as exc:
        print("CONTROLE ECHOUE : " + str(exc))
        sys.exit(1)

    for cle in sorted(rapport):
        print("  " + cle + " : " + str(rapport[cle]))

    print("")
    print("controle 8 : re-hash de la source apres traitement (verification non-modification)")
    sha_apres = sha256_fichier(args.source)
    print("  SHA-256 mesure  : " + sha_apres)
    if sha_apres != EXPECTED_SOURCE_SHA256:
        print("CONTROLE ECHOUE : la source a ete modifiee pendant l'execution du script.")
        sys.exit(1)
    print("  OK : source intacte")

    print("")
    print("TOUS LES CONTROLES (1 a 8) SONT VERIFIES OK.")
    sys.exit(0)


if __name__ == "__main__":
    main()
