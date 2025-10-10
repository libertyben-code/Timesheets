# Générateur de Planning d'Heures

Ce projet est une application Streamlit permettant de générer automatiquement des plannings d'heures pour différents codes de financement, selon une répartition mensuelle personnalisée. Elle propose la génération de plusieurs plannings à partir d'un fichier Excel.

---

## Fonctionnalités

- **Génération de plannings multiples** :  
  Importez un fichier Excel contenant plusieurs configurations (mois, année, jours fériés, contrats, etc.) pour générer automatiquement un fichier ZIP contenant tous les plannings.

- **Téléchargement d'un modèle Excel** :  
  Téléchargez un modèle à remplir pour préparer vos plannings en masse.

---

## Batch Upload (Génération de plannings multiples / Carga masiva)

La fonctionnalité de **batch upload** permet de générer plusieurs plannings/timesheets/horarios à partir d'un fichier Excel.

### Comment utiliser / How to use / Cómo usar

1. **Téléchargez le modèle Excel**  
   Cliquez sur le bouton pour télécharger la structure à remplir (les noms de colonnes changent selon la langue sélectionnée).

2. **Remplissez le fichier**  
   Chaque ligne doit contenir :
   - **Année / Year / Año** : ex. `2025`
   - **Mois / Month / Mes** : ex. `10`
   - **Heures par jour / Hours per day / Horas por día** : ex. `8`
   - **Jours fériés / Holidays / Días festivos** : liste séparée par des virgules, ex. `2025-10-01,2025-10-15`
   - **Contrats / Contracts / Contratos** : liste séparée par des virgules, ex. `FH71_01:50,FH71_02:50`
   - **Donor** : liste séparée par des virgules, ex. `Donor1,Donor2` (optionnel)

3. **Importez le fichier**  
   Utilisez le bouton d'import pour charger votre fichier Excel.

4. **Générez tous les plannings**  
   Cliquez sur le bouton pour générer tous les plannings/timesheets/horarios du fichier.

5. **Téléchargez le ZIP**  
   Un fichier ZIP contenant tous les plannings annuels sera proposé au téléchargement.

### Notes

- Les colonnes doivent correspondre à la langue sélectionnée.
- Les pourcentages de contrats doivent totaliser 100% sur chaque ligne.
- Les jours fériés doivent être au format `AAAA-MM-JJ` (`YYYY-MM-DD`).
- Les codes de financement et les donneurs sont associés dans l'ordre de la liste.

---

## Remarques

- Les jours fériés doivent être au format `AAAA-MM-JJ`.
- Les pourcentages de contrats doivent totaliser 100%.
- Les plannings sont générés de façon à respecter à la fois le total d'heures par jour et la répartition mensuelle par contrat.

---

## Technologies

- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Openpyxl](https://openpyxl.readthedocs.io/)

---

## Author

Vibe coded by Ben LIBERTY in Visual Studio Code use GPT-4.1