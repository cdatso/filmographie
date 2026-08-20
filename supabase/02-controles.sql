-- 02-controles.sql
-- Rejoue sur la table chargee les controles de outils/preparer-filmographie.py.
-- Prototype d'apprentissage BKL-FOR-003.
--
-- CONSOLIDE le 20/08/2026 (greffe, GATE-AH "go consolide 02") : le SQL
-- Editor de Supabase n'affiche que le resultat de la DERNIERE requete
-- d'un script (constat AH du 19/08 au soir) -- l'ancienne forme a une
-- requete par controle n'affichait donc que le dernier. La forme
-- consolidee rend LES DOUZE CONTROLES dans UN SEUL tableau
-- (ordre / controle / mesure / attendu) : mesure = attendu sur chaque
-- ligne, la table est certifiee. Le controle 0 (setval) est INCLUS :
-- il realigne la sequence d'identite sur max(id) -- sans lui, le
-- premier INSERT du temps 2 echouerait en collision de cle primaire.
-- CORRECTION du meme gate : l'attendu de l'ancien controle "Carnet de
-- notes" disait "exactement 1 ligne" -- FAUX (ecart de la session (a),
-- releve par AH le 19/08) : le LIKE attrape 2 films (Pasolini 1462 et
-- Wenders 1934, guillemets intacts). Attendu corrige : 2.

select 0 as ordre, 'setval (realigne la sequence)' as controle,
       setval(pg_get_serial_sequence('public.filmographie','id'),
              (select max(id) from public.filmographie))::text as mesure,
       '1998' as attendu
union all select 1, 'nb_lignes', count(*)::text, '1998' from public.filmographie
union all select 2, 'ids distincts', count(distinct id)::text, '1998' from public.filmographie
union all select 3, 'id min - max', min(id)::text || ' - ' || max(id)::text, '1 - 1998' from public.filmographie
union all select 4, 'annee vide', count(*)::text, '18' from public.filmographie where annee is null
union all select 5, 'annee_source vide', count(*)::text, '11' from public.filmographie where annee_source is null or annee_source = ''
union all select 6, 'duree_min vide', count(*)::text, '17' from public.filmographie where duree_min is null
union all select 7, 'muet vrai', count(*)::text, '107' from public.filmographie where muet = true
union all select 8, 'nb vrai', count(*)::text, '396' from public.filmographie where nb = true
union all select 9, 'categorie Film', count(*)::text, '1693' from public.filmographie where categorie = 'Film'
union all select 10, 'piege Terminator 2', count(*)::text, '1' from public.filmographie where titre_original = 'Terminator 2; Judgment Day'
union all select 11, 'pieges Carnet de notes', count(*)::text, '2 (Pasolini + Wenders)' from public.filmographie where titre like 'Carnet de notes%'
order by ordre;

-- DETAIL OPTIONNEL (a executer SEPAREMENT -- selectionner le bloc puis
-- Run ; lance avec tout le script, seul ce resultat s'afficherait) :
--
-- select id, realisateur, titre, titre_original
-- from public.filmographie
-- where titre_original = 'Terminator 2; Judgment Day'
--    or titre like 'Carnet de notes%'
-- order by id;
-- attendu : 3 lignes -- 802-ish Terminator 2 (le ; dans le titre
-- original), 1462 Pasolini, 1934 Wenders (guillemets conserves).
