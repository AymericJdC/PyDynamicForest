# Audit des dernières informations transmises par François Ningre

Date de l'audit : 13 novembre 2026

## Décision principale

La première année à considérer comme correspondant au maximum de compétition est **1985**, et non 1980.

La condition initiale principale candidate doit donc être reconstruite à l'inventaire de **1985**.

## Convention d'âge

Le fichier de synthèse de François donne :

- 1965 : âge 17 ;
- 1969 : âge 21 ;
- 1975 : âge 27 ;
- 1980 : âge 32 ;
- 1985 : âge 37 ;
- 1992 : âge 44 ;
- 1998 : âge 50 ;
- 2016 : âge 68 ;
- 2020 : âge 72.

Cette convention est cohérente avec une plantation en 1951 à l'âge de 3 ans : âge = année d'inventaire - 1951 + 3.

Le workflow historique de l'article utilise une convention décalée de +1 an pour plusieurs points (par exemple 1985 = 38 et 1992 = 45). La nouvelle simulation ne doit pas mélanger ces conventions. Le manuscrit devra annoncer explicitement la convention choisie et, si les labels historiques sont conservés dans les figures, documenter le décalage.

## Sources à utiliser

- Jusqu'à 1980 inclus : données GIS Coop.
- Après 1980 : série de François à privilégier pour les années retenues et les commentaires sur l'état des cimes.
- Les deux sources ne doivent pas être moyennées ou réconciliées silencieusement.

La série de synthèse retient : 1965, 1969, 1975, 1980, 1985, 1992, 1998, 2016 et 2020.

Les années 2001, 2007, 2010 et 2013 ne sont pas retenues dans la trajectoire principale, mais leurs données partielles de hauteur peuvent être utilisées pour ajuster et vérifier les allométries.

## Données de hauteur

Les hauteurs individuelles sont partielles, mais elles sont disponibles :

- dans le fichier GIS Coop pour les campagnes anciennes, notamment 1980 et 1985 ;
- dans le fichier de François pour A1, A2 et A5 en 2001, 2007, 2010, 2013, 2016 et 2020.

À A5, le fichier GIS Coop contient notamment :

- 1980 : 203 circonférences, 12 hauteurs d'échantillon, 9 valeurs `ht_vv` ;
- 1985 : 168 circonférences, 15 hauteurs d'échantillon, 15 valeurs `ht_vv` ;
- 1990 : 143 circonférences, 30 hauteurs d'échantillon ;
- 1992 : 139 circonférences, 21 hauteurs d'échantillon.

Le fichier de François contient pour A5 entre 21 et 29 couples circonférence-hauteur selon les campagnes 2001 à 2020. Des échantillons analogues existent pour A1 et A2.

Ces données rendent possible l'ajustement d'allométries hauteur-diamètre sur les trois placettes témoins A1, A2 et A5. Elles ne constituent pas des hauteurs complètes pour tous les arbres.

## Conséquence pour la condition initiale de 1985

La condition initiale ne doit plus être reconstruite par une copule gaussienne avant d'avoir exploité les hauteurs partielles de 1985 et les données des trois placettes.

La stratégie prioritaire devient :

1. ajuster une relation hauteur-diamètre pour 1985 en mobilisant A1, A2 et A5 ;
2. vérifier les effets placette et la cohérence des protocoles de hauteur ;
3. attribuer des hauteurs aux arbres d'A5 de 1985 ;
4. projeter conservativement le nuage individuel sur les grilles physique et native ;
5. utiliser une copule seulement comme analyse de sensibilité si l'allométrie ne suffit pas à représenter la dispersion ou la dépendance résiduelle.

## Points de vigilance

- Les protocoles de hauteur diffèrent selon les campagnes ; le fichier GIS Coop signale notamment un échantillon différent du protocole Coop en 1985.
- A5 a fait l'objet d'un nettoyage des arbres secs et chablis en 1981 ; cela doit être documenté dans l'interprétation de l'inventaire 1985.
- La surface est donnée comme 0,1216 ha pour les premières campagnes et 0,1200 ha dans la synthèse à partir de 1992. Cette différence doit être auditée avant les calculs définitifs de densité.
- Les commentaires de cime du fichier de François doivent être préférés pour les campagnes récentes.
- Les années 2001, 2007, 2010 et 2013 sont utiles pour les allométries, mais ne doivent pas être réintroduites automatiquement dans la trajectoire principale.

## Statut des scénarios

- **1985--2020** : nouveau scénario principal candidat, à construire sans recalibrer les paramètres dynamiques.
- **1992--2020** : scénario empirique reproductible déjà gelé ; conserver comme référence de contrôle et analyse de sensibilité au choix de la date initiale.
- **18--69 ans** : expérience historique hors domaine, destinée au supplément.
- **Copules Q-9C/Q-9D** : expérience méthodologique secondaire sous information agrégée.

## Prochaine étape

Avant toute nouvelle simulation :

1. figer le présent audit dans le dépôt ;
2. auditer quantitativement les échantillons hauteur-diamètre A1/A2/A5 ;
3. établir la convention d'âge officielle du scénario 1985 ;
4. trancher la surface 0,1216/0,1200 ha ;
5. ajuster et comparer un petit nombre d'allométries ;
6. reconstruire l'état initial empirique de 1985 ;
7. seulement alors lancer une unique trajectoire principale 1985--2020.
