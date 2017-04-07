# Foundational Model of Anatomy in an SQLite database

This repository contains python code to convert the CSV dump of the Foundational Model of Anatomy (FMA), available from [Bioportal](http://bioportal.bioontology.org/ontologies/FMA), to an SQLite database.  An SQLite database is also provided with a snapshot of a recent release of FMA.

The [FMA](http://si.washington.edu/projects/fma) is a mature ontology of anatomy created by the Structural Informatics Group at the University of Washington. The FMA was created in Protege, with complete ontological representations available in OWL or RDF/XML.  These representations are complete, but exceeding difficult to incorporate into small to medium sized software projects.

Bioportal also makes available a simplified CSV table of FMA's ontological terms.  This representation is very stripped down compared to the more complete ontological representations, but it does include all of the terms in the ontology along with some useful relationships.  For applications such as unique naming, this flattened representation is ideal.

To further improve the utility of this tabular FMA representation, we have converted the CSV format into an SQLite database.  This form allows rapid search over the database on almost any software platform.  

The fma-sqlite is stripped down even further from the CSV version.  Columns that were uniformly NULL or had only a few values have been dropped.  The choice of which columns were retained or not was somewhat arbitrary and can always be revisited.  The remaining columns are mapped to a consistent lowercase naming convention.  Here are the columns that remain, along with their mappings to the original CSV:

 * `id` (derived from Class ID)
 * `name` (from Preferred Label)
 * `parent_id` (numeric FMA ID or NULL if not in FMA)
 * `aal` (see [Anatomical Automatic Labeling](http://www.cyceron.fr/index.php/en/plateforme-en/freeware))

In addition, several fields of the original CSV have multiple values (`definitions`, `dk_freesurfer`, and `talairach`).  These columns have been broken out into their own tables with each row representing one value.  

A special synonyms table provides a mapping from FMAID to every name in the database for that ID, including `synonym`, `preferred_label`, and `non_english_equivalent`. Additional fields describe the source and language of the synonym (if known).

Finally, a hierarchy table provides a mapping of FMAID to each of the term's ancestors, with an additional column providing the distance in the tree.  This table allows efficient subtree searching.

**No indexes are included to keep the database small, but creating indexes based on application requirements is highly recommended.**

Here is the schema for the tables in the database:
```
CREATE TABLE fma
        (id integer NOT NULL PRIMARY KEY,
         name text,
         parent_id integer,  -- can be NULL for top level
         aal integer);
CREATE TABLE synonyms
        (id integer NOT NULL,
        name text,
        synonym text,
        synonym_type text,  -- what column the name came from
        lang text,          -- if known
        foreign key(id) references fma(id));
CREATE TABLE definitions
        (id integer NOT NULL,
        name text,
        definition text,
        lang text);
CREATE TABLE fma_dk_freesurfer
        (id integer NOT NULL,
        dk_freesurfer integer NOT NULL,
        foreign key(id) references fma(id));
CREATE TABLE fma_talairach
        (id integer NOT NULL,
        talairach integer NOT NULL,
        foreign key(id) references fma(id));
CREATE TABLE hierarchy
        (id integer NOT NULL,
        ancestor_id integer NOT NULL,
        hierarchy_level integer,
        foreign key(id) references fma(id));
```