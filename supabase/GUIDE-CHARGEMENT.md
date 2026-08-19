# Guide de chargement — filmographie vers Supabase

Ce guide est pour toi, AH. Il liste tes quatre gestes, dans l'ordre. Rien
ici ne se fait automatiquement : la préparation s'arrête à ce point, le
chargement dans Supabase est ton geste, sur ton compte.

## ① Créer la table

Projet Supabase `cdatso` → **SQL Editor** → colle le contenu de
`supabase\01-table-filmographie.sql` → **Run**.

Ce script crée la table `filmographie` (11 colonnes + `id` + `created_at`),
active la RLS (row level security) et ajoute une seule policy : lecture
publique (SELECT) pour le rôle `anon`. Aucun INSERT/UPDATE/DELETE public.

> **Amendement du 19/08 23h5x (greffe, sur ta demande)** : la table accepte
> désormais une colonne **`id` fournie par le CSV** (première colonne,
> 1→1998). Rejoue le geste ① **en entier** (le script commence par un
> `drop table` : il repart de zéro), importe un CSV **portant la colonne
> id**, puis au geste ③ exécute d'abord le **contrôle 0** (`setval`) de
> `02-controles.sql`.

## ② Importer les données

Projet `cdatso` → **Table Editor** → table `filmographie` → **Insert** →
**Import data from CSV** → sélectionne :

`C:\Users\cdats\Claude\Projects\filmographie\donnees\filmographie-utf8.csv`

1 998 lignes, encodage UTF-8 sans BOM, séparateur virgule (RFC4180). Si
l'importeur te propose un mapping de colonnes, vérifie qu'il retient les
11 noms de colonnes tels quels (`realisateur`, `titre`, … `pays`).

## ③ Vérifier

Projet `cdatso` → **SQL Editor** → colle et exécute
`supabase\02-controles.sql`, requête par requête. Chaque requête porte son
attendu en commentaire — compare le résultat affiché à l'attendu écrit
juste au-dessus. Le premier écart est à signaler, pas à corriger seul(e).

## ④ Relever les paramètres du temps (b)

Projet `cdatso` → **Settings** → **API** → relève et garde de côté :

- l'**URL du projet** (`https://<ref>.supabase.co`) ;
- la clé **`anon`** (`public`).

Ces deux valeurs seront les paramètres du mandat (b), qui génère la page
publique.

**⚠️ Borne** : la clé **`service_role` ne sort jamais du dashboard** — ni
dans un dépôt, ni dans un script, ni dans le chat. La clé `anon` est faite
pour un client public ; c'est la RLS (étape ①), pas le secret de cette
clé, qui protège la table contre l'écriture.
