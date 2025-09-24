-- GameQuest Database Schema
-- Generated on: 2025-09-22 23:12:08
-- Migrated from local PostgreSQL to Neon

CREATE TABLE critics (
    review_id integer NOT NULL,
    game_id integer,
    game_title text,
    citation text
);

ALTER TABLE critics ADD PRIMARY KEY (review_id);

CREATE TABLE games (
    id integer NOT NULL,
    title text NOT NULL,
    description text,
    release_date date,
    moby_score double precision,
    moby_url text,
    platforms ARRAY,
    genres ARRAY,
    developers ARRAY,
    publishers ARRAY,
    sample_cover_url text,
    sample_screenshot_urls ARRAY
);

ALTER TABLE games ADD PRIMARY KEY (id);

CREATE TABLE games_with_critics (
    id integer,
    title text,
    description text,
    release_date date,
    moby_score double precision,
    moby_url text,
    platforms ARRAY,
    genres ARRAY,
    developers ARRAY,
    publishers ARRAY,
    sample_cover_url text,
    sample_screenshot_urls ARRAY,
    critic_count bigint
);

CREATE VIEW games_with_critics AS  SELECT g.id,
    g.title,
    g.description,
    g.release_date,
    g.moby_score,
    g.moby_url,
    g.platforms,
    g.genres,
    g.developers,
    g.publishers,
    g.sample_cover_url,
    g.sample_screenshot_urls,
    count(c.review_id) AS critic_count
   FROM (games g
     LEFT JOIN critics c ON ((g.id = c.game_id)))
  GROUP BY g.id, g.title, g.description, g.release_date, g.moby_score, g.moby_url, g.platforms, g.genres, g.developers, g.publishers, g.sample_cover_url, g.sample_screenshot_urls;;
