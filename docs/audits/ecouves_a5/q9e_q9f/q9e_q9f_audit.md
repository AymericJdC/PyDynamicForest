# Audit numerique consolide Q-9E/Q-9F - Ecouves A5

**Date:** 2026-10-23T16:41:34+02:00  
**Branche:** `feature/observation-quadrature`  
**HEAD:** `0862d0270f3f04413d13f7f9880b56f0e5f3c33e`  
**Tests:** 71 tests uniques reussis; suite complete en 1.92 s; sous-ensemble Q-9F.7 de 4 tests reexecute en 0.76 s.

## 1. Conclusion

Le pipeline empirique Q-9E/Q-9F est versionne, testable et couvert de l'audit des inventaires jusqu'aux diagnostics numeriques. La trajectoire principale 1992-2020, ages GIS Coop 45-73, est complete. Les parametres dynamiques n'ont pas ete recalibres sur Ecouves A5.

Q-9F.7 reste une experience numerique rejetee pour non-conservation. Elle est archivee sans interpretation biologique et ne doit pas etre integree au scenario principal.

## 2. Etat Git

```text
M simulations/article/observations.py
 M tests/test_article_observations.py
?? audit_q9e_q9f.py
?? consolidate_q9e_q9f_audit.py
?? q9e_q9f_audit.md
?? q9e_q9f_components.csv
?? q9e_q9f_outputs.csv
```

L'audit consolide contient 69 composants reels apres exclusion des caches Python, dont 67 suivis par Git et 14 fichiers de tests.

## 3. Tests

Le total correct est **71 tests uniques**, et non 75. La premiere execution affichait deja 71 tests; les 4 tests de sensibilite Q-9F.7 ont ensuite ete reexecutes separement. Ils ne doivent pas etre comptes deux fois.

- suite Q-9E/Q-9F: `71 passed in 1.92s`;
- reexecution ciblee Q-9F.7: `4 passed in 0.76s`;
- echec: aucun.

## 4. Pipeline empirique principal

- Q-9E.1: audit et reconciliation de neuf inventaires, 1965-2020, avec anomalie 2013 conservee explicitement;
- Q-9E.2: interface generique et remplacable de fournisseur de hauteurs;
- Q-9E.3: reconstruction deterministe provisoire des hauteurs par la relation de Savine;
- Q-9E.4: projection conservative sur grille physique 101 x 161;
- Q-9E.5: conversion conservative vers les etats natifs 40 x 40;
- Q-9F.1: controle dynamique court intentionnel depuis 1992;
- Q-9F.2: trajectoire principale complete 1992-2020, ages 45-73;
- Q-9F.3: diagnostics distributionnels;
- Q-9F.4: screening mecanistique OAT local, sans pretention d'identifiabilite;
- Q-9F.5: diagnostic de la hierarchie des hauteurs;
- Q-9F.6: audit de l'allocation verticale de la croissance;
- Q-9F.7: transformation du statut rejetee pour non-conservation.

## 5. Entrees externes

2 classeurs locaux ne sont pas suivis par Git:

- `data/article/ecouves_a5/raw/Ecouves-A5.xlsx`; SHA-256 `07f9c2796f249840daecbf4a35efe9ed673ccc9c3601c0330017db4edc97eee0`.
- `data/article/ecouves_a5/reference/Douglas2021(116obs).xlsx`; SHA-256 `4df4a3e0a4515d18219073acd1c192057173aa9760e67b4d31e1438dce56431a`.

Ils ne doivent pas etre ajoutes automatiquement au depot. Leur provenance, leurs conditions d'acces et leurs empreintes doivent etre conservees.

## 6. Sorties

Les 80 fichiers inventories couvrent les douze repertoires Q-9E/Q-9F. Les `.gitkeep` sont des marqueurs de repertoire et non des sorties vides ou inachevees. Les etats NPZ intermediaires sont des artefacts attendus, pas des simulations interrompues.

La trajectoire principale atteint l'age demande 73 et l'age numerique 72.99899999999326 avec `dt = 0.0051`. Les etats 1992, 1998, 2016 et 2020 sont presents.

## 7. Decisions

### Conserver dans le pipeline principal

Les composants Q-9E.1 a Q-9F.6, leurs tests, leurs documents et les manifestes ou metadonnees de reproductibilite.

### Comparer avant factorisation avec Q-9C/Q-9D

- injection et validation de `U0`;
- projections conservatives;
- isolation et protection des sorties;
- metadonnees et manifestes;
- operateurs d'observation;
- orchestration des trajectoires;
- tests legers d'horizon, masse, finitude et non-negativite.

### Archiver separement

Q-9F.7, ses scripts, tests, rapports et sorties, comme experience rejetee. Aucun resultat transforme ne doit alimenter le manuscrit principal.

### Ne pas supprimer maintenant

Aucun composant scientifique avant comparaison architecturale et constitution des archives. Les caches Python peuvent etre supprimes librement; ils sont exclus des CSV consolides.

## 8. Etape suivante

1. Commiter cet audit consolide dans `docs/audits/ecouves_a5/q9e_q9f/`.
2. Auditer les modifications en cours de `simulations/article/observations.py` et `tests/test_article_observations.py` dans leur chantier propre.
3. Comparer les architectures Q-9C/Q-9D et Q-9E/Q-9F.
4. Factoriser uniquement les briques communes confirmees.
5. Figer le scenario empirique principal et preparer le manuscrit et le supplement.
