import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import date, timedelta, datetime
from io import BytesIO

# =============================
# Fonctions auxiliaires
# =============================

def get_all_days(mois, annee):
    jours = []
    current_date = date(annee, mois, 1)
    while current_date.month == mois:
        jours.append(current_date)
        current_date += timedelta(days=1)
    return jours

def get_jours_ouvres(mois, annee, jours_feries):
    all_days = get_all_days(mois, annee)
    jours_ouvres = [d for d in all_days if d.weekday() < 5 and d not in jours_feries]
    return jours_ouvres

def generer_excel(mois_selectionne, annee_selectionnee, contrats, heures_par_jour, jours_feries):
    jours_mois = get_all_days(mois_selectionne, annee_selectionnee)
    jours_ouvres = get_jours_ouvres(mois_selectionne, annee_selectionnee, jours_feries)
    nb_jours_ouvres = len(jours_ouvres)
    HEURES_TOTALES = nb_jours_ouvres * heures_par_jour

    # Target monthly hours per contract
    heures_cibles = {code: round(HEURES_TOTALES * pct / 100, 2) for code, pct in contrats.items()}
    contrats_list = list(contrats.keys())

    # Initialize DataFrame
    df_repartition = pd.DataFrame(index=contrats_list, columns=jours_mois, dtype=float)
    df_repartition[:] = 0.0

    # Remaining hours per contract
    heures_restantes = heures_cibles.copy()

    # Allocate hours day by day
    for jour in jours_mois:
        if jour.weekday() >= 5 or jour in jours_feries:
            df_repartition[jour] = np.nan  # <-- FIX: use np.nan instead of ""
            continue

        # Calculate max allocatable for each contract (cannot exceed remaining)
        max_alloc = [min(heures_restantes[code], heures_par_jour) for code in contrats_list]

        # Use random splits that sum to heures_par_jour, but do not exceed max_alloc
        rng = np.random.default_rng()
        while True:
            # Generate random proportions
            props = rng.dirichlet(np.ones(len(contrats_list)))
            alloc = np.minimum(np.round(props * heures_par_jour * 2) / 2, max_alloc)
            # Adjust if sum is not heures_par_jour due to min/max
            diff = heures_par_jour - alloc.sum()
            if abs(diff) < 0.01:
                break
            # Try to adjust the largest contract
            idx = np.argmax(max_alloc)
            if alloc[idx] + diff <= max_alloc[idx] and alloc[idx] + diff >= 0:
                alloc[idx] += diff
                break

        # Assign and update remaining
        for idx, code in enumerate(contrats_list):
            df_repartition.loc[code, jour] = alloc[idx]
            heures_restantes[code] -= alloc[idx]

    df_repartition.loc["Total/jour"] = df_repartition.sum(axis=0)
    df_repartition["Total contrat"] = df_repartition.sum(axis=1)

    # Création Excel en mémoire
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_contrats = pd.DataFrame({
            "Code financement": contrats_list,
            "Pourcentage": [contrats[code] for code in contrats_list]
        })
        df_contrats.to_excel(writer, sheet_name="Répartition", index=False, startrow=1)
        df_repartition.to_excel(writer, sheet_name="Planning", index=True, startrow=1)

    output.seek(0)
    return output

# =============================
# Interface Streamlit
# =============================

st.set_page_config(page_title="Générateur de Planning", layout="centered")

st.title("📅 Générateur de planning d'heures")

# Sélection du mois et année
col1, col2 = st.columns(2)
with col1:
    mois_nom = st.selectbox("Mois", list(calendar.month_name)[1:], index=9)
with col2:
    annee = st.number_input("Année", min_value=2020, max_value=2100, value=2025)

mois = list(calendar.month_name).index(mois_nom)

# Heures par jour
heures_par_jour = st.slider("Heures par jour ouvré", 1, 12, 8)

# Entrée des jours fériés
st.subheader("Jours fériés")
jours_feries_input = st.text_area(
    "Entrez les jours fériés du mois (format AAAA-MM-JJ), un par ligne, ex:\n2025-10-01\n2025-10-15",
    height=100
)

jours_feries = []
for ligne in jours_feries_input.split('\n'):
    ligne = ligne.strip()
    if ligne:
        try:
            dt = datetime.strptime(ligne, "%Y-%m-%d").date()
            jours_feries.append(dt)
        except Exception:
            st.error(f"Format de date invalide : {ligne}")

# Tableau des contrats
st.subheader("Répartition par contrat")
nb_contrats = st.number_input("Nombre de contrats", min_value=1, max_value=10, value=3)
contrats = {}

for i in range(nb_contrats):
    cols = st.columns([2, 1])
    code = cols[0].text_input(f"Code financement {i+1}", value=f"FH71_0{i+1}")
    pct = cols[1].number_input(f"%", min_value=0.0, max_value=100.0, value=round(100/nb_contrats, 2), step=1.0, key=f"pct_{i}")
    if code:
        contrats[code] = pct

# Vérification total
total_pct = sum(contrats.values())
if total_pct != 100:
    st.error(f"❌ Le total des pourcentages est {total_pct}%. Il doit être égal à 100%.")
    st.stop()

# Génération
if st.button("✅ Générer le planning"):
    excel_file = generer_excel(mois, annee, contrats, heures_par_jour, jours_feries)
    file_name = f"planning_{mois_nom}_{annee}.xlsx"

    st.success("Fichier Excel généré avec succès !")
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=excel_file,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
