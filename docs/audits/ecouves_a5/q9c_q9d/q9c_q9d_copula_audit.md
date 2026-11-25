# Audit numerique consolide Q-9C/Q-9D - Ecouves A5

**Date de consolidation :** 2026-10-23T16:33:13+02:00  
**Branche :** `feature/observation-quadrature`  
**HEAD :** `97d235f8c6d8c7baf0247b8fcc7768aca9b78991`  
**Commit d'archivage :** `97d235f8c6d8c7baf0247b8fcc7768aca9b78991`  
**Date du commit :** `2026-10-23T16:29:23+02:00`  
**Objet :** `archive Q-9C Q-9D copula experiments and tests`  
**Tests cibles :** `14 passed in 1.68s`

## 1. Conclusion

Q-9C/Q-9D est desormais securise, versionne et teste. Les scripts et tests historiques ont ete archives dans Git et les 14 tests cibles passent. Aucune simulation complete ni recalibration n'a ete lancee pendant l'audit.

La reconstruction par copule devient une experience methodologique secondaire sous information agregee. Q-9E/Q-9F reste la voie principale fondee sur les inventaires individuels.

## 2. Etat Git

Le commit `97d235f8c6d8c7baf0247b8fcc7768aca9b78991` archive les composants Q-9C/Q-9D. Les modifications encore presentes dans `simulations/article/observations.py` et `tests/test_article_observations.py` restent hors de cette archive.

```text
M simulations/article/observations.py
 M tests/test_article_observations.py
?? audit_q9c_q9d.py
?? consolidate_q9c_q9d_audit.py
?? q9c_q9d_components.csv
?? q9c_q9d_copula_audit.md
?? q9c_q9d_outputs.csv
```

## 3. Tests

```text
.............. [100%]
14 passed in 1.68s
```

Les cinq fichiers de tests sont collectables et executables. Ce resultat ne constitue pas une nouvelle execution des trajectoires completes.

## 4. Reconstruction initiale Q-9C

Les familles d'etats compatibles aux ages GIS Coop 38 et 45 sont preservees pour sept valeurs de `rho` entre 0.50 et 0.95. Elles documentent la non-identifiabilite entre `rho` et la dispersion marginale des hauteurs sous observations agregees.

## 5. Trajectoires Q-9D

Les trajectoires `rho = 0.50`, `0.85` et `0.95`, commencees a l'age 45, sont completes jusqu'a l'age 69. Les fichiers `state_age_*.npz` sont des etats initiaux, intermediaires ou finaux et non des simulations incompletes. `rho_0.85_smoke_10_steps` est une execution courte intentionnelle.

La reconstruction initiale a 38 ans existe, mais la trajectoire dynamique depuis 38 ans n'est pas archivee sous `outputs/article_scenarios/transition_age38/`. Aucun recalcul n'est recommande.

## 6. Screening OAT

Le screening historique couvre les perturbations de croissance en hauteur, croissance diametrique, diffusion et mortalite. Le scenario de reference et les perturbations +/-20 % sont conserves comme ensemble historique complet jusqu'a l'age 69.

## 7. Decisions

### Conserver

- tests historiques ;
- manifestes et metadonnees de reproductibilite ;
- controles de masse, finitude et non-negativite ;
- resumes scientifiques.

### Reutiliser apres comparaison avec Q-9E/Q-9F

- injection d'une matrice `U0` ;
- isolation des sorties et protection contre l'ecrasement ;
- manifestes et metadonnees ;
- operateurs d'observation ;
- comparaisons multi-scenarios ;
- tests legers d'horizon et d'etat initial.

### Archiver comme experience methodologique

- reconstruction par copule ;
- familles d'etats compatibles ;
- trajectoires multi-`rho` ;
- screening OAT historique ;
- analyse de non-identifiabilite.

### Suppression

Aucun composant n'est autorise a la suppression avant constitution et verification d'une archive methodologique.

## 8. Corrections de la premiere passe

- statut Git mis a jour apres commit ;
- resultat reel des tests ajoute ;
- `step_index` exclu du diagnostic d'age ;
- instantanes distingues des simulations incompletes ;
- smoke test distingue d'une interruption ;
- trajectoires 45-69 reconnues completes ;
- screening OAT reconnu complet ;
- seule la transition dynamique depuis 38 ans reste absente.

## 9. Suite

1. Auditer Q-9E/Q-9F.
2. Comparer les architectures copule et empirique.
3. Factoriser seulement les briques communes confirmees.
4. Figer le scenario empirique principal 1992-2020, ages 45-73.
5. Mettre a jour le manuscrit et le supplement.
6. Constituer l'archive methodologique Q-9C/Q-9D.
