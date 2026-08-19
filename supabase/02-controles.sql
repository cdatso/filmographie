-- 02-controles.sql
-- Rejoue sur la table chargee les controles de outils/preparer-filmographie.py.
-- Chaque requete porte son attendu en commentaire -- une requete sans
-- attendu ne controle rien. A executer dans le SQL Editor de Supabase
-- APRES l'import CSV, et a comparer ligne a ligne avec les attendus.

-- attendu : 1998
select count(*) as nb_lignes
from public.filmographie;

-- attendu : 18
select count(*) as annee_vide
from public.filmographie
where annee is null;

-- attendu : 11
select count(*) as annee_source_vide
from public.filmographie
where annee_source is null or annee_source = '';

-- attendu : 17
select count(*) as duree_min_vide
from public.filmographie
where duree_min is null;

-- attendu : 107
select count(*) as muet_vrai
from public.filmographie
where muet = true;

-- attendu : 396
select count(*) as nb_vrai
from public.filmographie
where nb = true;

-- attendu : Film = 1693 en tete de liste (ordre decroissant)
select categorie, count(*) as nb
from public.filmographie
group by categorie
order by nb desc;

-- attendu : exactement 1 ligne, titre_original = 'Terminator 2; Judgment Day'
select id, realisateur, titre, titre_original
from public.filmographie
where titre_original = 'Terminator 2; Judgment Day';

-- attendu : exactement 1 ligne, titre commencant par 'Carnet de notes'
-- (guillemets internes conserves autour de Vetements et villes)
select id, realisateur, titre
from public.filmographie
where titre like 'Carnet de notes%';
