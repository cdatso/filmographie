# filmographie

**Statut : prototype d'apprentissage.** Préparé en amont de l'atelier
AI-Shift du 26/08/2026 (Creagora, Namur), dont la chaîne technique
imposée est : repo GitHub + backend Supabase + déploiement Netlify. Ce
dépôt parcourt la même chaîne à froid, sur une matière qui appartient à
AH, avant le jour J.

Question de fin explicite, non tranchée ici : garder / migrer / éteindre.

## La chaîne, en quatre temps

1. **CSV source** (chez AH, hors de ce dépôt) — un export de filmographie,
   encodage CP1252, séparateur `;`.
2. **Préparation** — `outils\preparer-filmographie.py` convertit vers
   `donnees\filmographie-utf8.csv` (UTF-8 sans BOM, RFC4180, 11 colonnes
   typées).
3. **Table Supabase** — `supabase\` contient le script de création de
   table, les contrôles post-import et le guide de chargement.
4. **Page statique** — `index.html`, à la racine de ce dépôt, régénérée
   par `outils\generer-page.py` depuis la table Supabase (lecture seule,
   `GET` uniquement). Publiée sous
   `https://www.cdatso.be/filmographie/` (geste d'AH : création du dépôt
   GitHub, remote, push, activation de Pages — voir la note de remise du
   temps (b), `claude-config\mandats\FOR\BKL-FOR-003\`).

**La source de vérité est la table Supabase.** La page publique n'en est
qu'un dérivé, régénérable — jamais éditée à la main.

### Régénérer la page

```
python outils\generer-page.py --acces <chemin du fichier hors dépôt contenant l'URL et la clé publique>
```

ou, sans fichier d'accès :

```
python outils\generer-page.py --url <URL du projet Supabase> --cle <clé publique>
```

Le script pagine automatiquement, ne rend rien tant que le total mesuré
n'est pas confirmé, et écrit `index.html` à la racine du dépôt (aucun
paramètre `--sortie` requis pour le cas normal). Aucune valeur de clé
n'est fournie ici : la clé publique (`publishable`, remplaçante de
l'ancienne clé `anon`) reste dans le fichier d'accès hors dépôt.

## Portée

Structure plate (temps 1). La transformation relationnelle (tables
liées, jointures, vues) est un temps 2, hors périmètre de ce dépôt à ce
stade.

Ce dépôt ne contient aucune donnée de compte, aucun chemin de compte,
aucune clé.
