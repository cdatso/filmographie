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
4. **Page statique** — régénérable à partir de la table (mandat séparé,
   temps (b) de BKL-FOR-003).

**La source de vérité est la table Supabase.** La page publique n'en est
qu'un dérivé, régénérable.

## Portée

Structure plate (temps 1). La transformation relationnelle (tables
liées, jointures, vues) est un temps 2, hors périmètre de ce dépôt à ce
stade.

Ce dépôt ne contient aucune donnée de compte, aucun chemin de compte,
aucune clé.
