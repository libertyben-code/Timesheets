# Générateur de Planning d'Heures

Ce projet est une application Streamlit permettant de générer automatiquement des plannings d'heures pour différents codes de financement, selon une répartition mensuelle personnalisée. Elle propose la génération d'un planning unique ou de plusieurs plannings à partir d'un fichier Excel.

---

## Fonctionnalités

- **Génération d'un planning unique** :  
  Saisissez le mois, l'année, le nombre d'heures par jour ouvré, les jours fériés et la répartition des pourcentages par contrat pour obtenir un fichier Excel prêt à l'emploi.

- **Génération de plannings multiples** :  
  Importez un fichier Excel contenant plusieurs configurations (mois, année, jours fériés, contrats, etc.) pour générer automatiquement un fichier ZIP contenant tous les plannings.

- **Téléchargement d'un modèle Excel** :  
  Téléchargez un modèle à remplir pour préparer vos plannings en masse.

---

## Utilisation

### 1. Générer un planning unique

1. **Sélectionnez le mois et l'année**.
2. **Choisissez le nombre d'heures par jour ouvré** (slider).
3. **Indiquez les jours fériés** du mois (un par ligne, format `AAAA-MM-JJ`).
4. **Définissez la répartition par contrat** :
   - Indiquez le code de financement et le pourcentage pour chaque contrat.
   - Le total des pourcentages doit être égal à 100%.
5. Cliquez sur **"✅ Générer le planning"**.
6. Téléchargez le fichier Excel généré.

---

### 2. Générer plusieurs plannings via Excel

1. Cliquez sur **"📥 Télécharger le modèle Excel"** pour obtenir le modèle à remplir.
2. Remplissez le fichier avec vos différentes configurations :
   - **Année** : ex. `2025`
   - **Mois** : ex. `10`
   - **Heures par jour** : ex. `8`
   - **Jours fériés** : liste séparée par des virgules, ex. `2025-10-01,2025-10-15`
   - **Contrats** : liste séparée par des virgules, ex. `FH71_01:50,FH71_02:50`
3. Importez le fichier via le bouton d'import.
4. Cliquez sur **"✅ Générer tous les plannings du fichier"**.
5. Téléchargez le fichier ZIP contenant tous les plannings générés.

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
