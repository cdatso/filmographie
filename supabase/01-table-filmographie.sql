-- 01-table-filmographie.sql
-- Cree la table filmographie et active le controle d'acces (RLS).
-- Prototype d'apprentissage BKL-FOR-003 -- executable tel quel dans le
-- SQL Editor de Supabase, PostgreSQL standard.

create table public.filmographie (
    id bigint generated always as identity primary key,
    realisateur text,
    titre text,
    titre_original text,
    categorie text,
    muet boolean not null,
    nb boolean not null,
    duree_min integer null,
    annee integer null,
    annee_source text,
    genres_sc text,
    pays text,
    created_at timestamptz not null default now()
);

-- Active le controle d'acces ligne par ligne : sans policy, personne ne
-- lit ni n'ecrit -- meme pas via la clef anon.
alter table public.filmographie enable row level security;

-- Seule policy : lecture publique (SELECT) pour le role anon.
-- Aucun INSERT, UPDATE ni DELETE public -- c'est la RLS qui protege,
-- pas le secret de la clef anon.
create policy "lecture publique filmographie"
    on public.filmographie
    for select
    to anon
    using (true);
