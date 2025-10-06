import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import date, timedelta, datetime
from io import BytesIO
import zipfile

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
# Language toggle (flags)
# =============================

from streamlit import markdown

LANGUAGES = {
    "Français": "🇫🇷",
    "English": "🇬🇧",
    "Español": "🇪🇸"
}

lang_labels = [f"{LANGUAGES[l]} {l}" for l in LANGUAGES]
lang_map = dict(zip(lang_labels, LANGUAGES.keys()))

st.markdown(
    """
    <style>
    .block-container {padding-top: 1rem;}
    </style>
    """,
    unsafe_allow_html=True
)

selected_lang_label = st.radio(
    label="",
    options=lang_labels,
    horizontal=True
)
lang = lang_map[selected_lang_label]
is_fr = lang == "Français"
is_en = lang == "English"
is_es = lang == "Español"

# =============================
# Interface Streamlit
# =============================

st.set_page_config(
    page_title=(
        "Générateur de Planning" if is_fr else
        "Timesheet Generator" if is_en else
        "Generador de Horarios"
    ),
    layout="centered"
)

st.title(
    "📅 Générateur de planning d'heures" if is_fr else
    "📅 Timesheet Generator" if is_en else
    "📅 Generador de horarios"
)

template = BytesIO()
df_template = pd.DataFrame({
    "Année" if is_fr else "Year" if is_en else "Año": [2025],
    "Mois" if is_fr else "Month" if is_en else "Mes": [10],
    "Heures par jour" if is_fr else "Hours per day" if is_en else "Horas por día": [8],
    "Jours fériés" if is_fr else "Holidays" if is_en else "Días festivos": ["2025-10-01,2025-10-15"],
    "Contrats" if is_fr else "Contracts" if is_en else "Contratos": ["FH71_01:50,FH71_02:50"]
})
with pd.ExcelWriter(template, engine="openpyxl") as writer:
    df_template.to_excel(writer, index=False)
template.seek(0)
st.download_button(
    label=(
        "📥 Télécharger le modèle Excel" if is_fr else
        "📥 Download Excel template" if is_en else
        "📥 Descargar plantilla Excel"
    ),
    data=template,
    file_name=(
        "modele_plannings.xlsx" if is_fr else
        "timesheet_template.xlsx" if is_en else
        "plantilla_horarios.xlsx"
    ),
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Upload multiple plannings
st.subheader(
    "Importer un fichier Excel pour plusieurs plannings" if is_fr else
    "Upload an Excel file for multiple timesheets" if is_en else
    "Subir un archivo Excel para varios horarios"
)
uploaded_file = st.file_uploader("", type=["xlsx"])

if uploaded_file:
    df_upload = pd.read_excel(uploaded_file)
    st.write(
        "Aperçu du fichier importé :" if is_fr else
        "Preview of uploaded file:" if is_en else
        "Vista previa del archivo subido:"
    )
    st.dataframe(df_upload)

    if st.button(
        "✅ Générer tous les plannings du fichier" if is_fr else
        "✅ Generate all timesheets from file" if is_en else
        "✅ Generar todos los horarios del archivo"
    ):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for idx, row in df_upload.iterrows():
                try:
                    annee = int(row["Année"] if is_fr else row["Year"] if is_en else row["Año"])
                    mois = int(row["Mois"] if is_fr else row["Month"] if is_en else row["Mes"])
                    heures_par_jour = int(row["Heures par jour"] if is_fr else row["Hours per day"] if is_en else row["Horas por día"])
                    jours_feries = []
                    jours_feries_col = "Jours fériés" if is_fr else "Holidays" if is_en else "Días festivos"
                    if pd.notna(row.get(jours_feries_col, None)):
                        for d in str(row[jours_feries_col]).split(","):
                            d = d.strip()
                            if d:
                                jours_feries.append(datetime.strptime(d, "%Y-%m-%d").date())
                    contrats = {}
                    contrats_col = "Contrats" if is_fr else "Contracts" if is_en else "Contratos"
                    for item in str(row[contrats_col]).split(","):
                        code, pct = item.split(":")
                        contrats[code.strip()] = float(pct.strip())
                    if sum(contrats.values()) != 100:
                        continue  # skip invalid rows
                    excel_file = generer_excel(mois, annee, contrats, heures_par_jour, jours_feries)
                    file_name = (
                        f"planning_{mois}_{annee}_{idx+1}.xlsx" if is_fr else
                        f"timesheet_{mois}_{annee}_{idx+1}.xlsx" if is_en else
                        f"horario_{mois}_{annee}_{idx+1}.xlsx"
                    )
                    zipf.writestr(file_name, excel_file.getvalue())
                except Exception as e:
                    st.warning(
                        f"Ligne {idx+1} ignorée : {e}" if is_fr else
                        f"Row {idx+1} skipped: {e}" if is_en else
                        f"Fila {idx+1} omitida: {e}"
                    )

        zip_buffer.seek(0)
        st.success(
            "Tous les plannings ont été générés !" if is_fr else
            "All timesheets have been generated!" if is_en else
            "¡Todos los horarios han sido generados!"
        )
        st.download_button(
            label=(
                "📥 Télécharger le ZIP des plannings" if is_fr else
                "📥 Download ZIP of timesheets" if is_en else
                "📥 Descargar ZIP de horarios"
            ),
            data=zip_buffer,
            file_name=(
                "plannings.zip" if is_fr else
                "timesheets.zip" if is_en else
                "horarios.zip"
            ),
            mime="application/zip"
        )

# Sélection du mois et année

st.subheader(
    "Générer un planning unique" if is_fr else
    "Generate a single timesheet" if is_en else
    "Generar un horario único"
)
col1, col2 = st.columns(2)
with col1:
    mois_nom = st.selectbox(
        "Mois" if is_fr else "Month" if is_en else "Mes",
        list(calendar.month_name)[1:], index=9
    )
with col2:
    annee = st.number_input(
        "Année" if is_fr else "Year" if is_en else "Año",
        min_value=2020, max_value=2100, value=2025
    )

mois = list(calendar.month_name).index(mois_nom)

# Heures par jour
heures_par_jour = st.slider(
    "Heures par jour ouvré" if is_fr else
    "Hours per working day" if is_en else
    "Horas por día laboral",
    1, 12, 8
)

# Entrée des jours fériés
st.subheader(
    "Jours fériés" if is_fr else
    "Holidays" if is_en else
    "Días festivos"
)
jours_feries_input = st.text_area(
    "Entrez les jours fériés du mois (format AAAA-MM-JJ), un par ligne, ex:\n2025-10-01\n2025-10-15"
    if is_fr else
    "Enter holidays for the month (format YYYY-MM-DD), one per line, e.g.:\n2025-10-01\n2025-10-15"
    if is_en else
    "Ingrese los días festivos del mes (formato AAAA-MM-DD), uno por línea, ej.:\n2025-10-01\n2025-10-15",
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
            st.error(
                f"Format de date invalide : {ligne}" if is_fr else
                f"Invalid date format: {ligne}" if is_en else
                f"Formato de fecha inválido: {ligne}"
            )

# Tableau des contrats
st.subheader(
    "Répartition par contrat" if is_fr else
    "Contract allocation" if is_en else
    "Distribución por contrato"
)
nb_contrats = st.number_input(
    "Nombre de contrats" if is_fr else
    "Number of contracts" if is_en else
    "Número de contratos",
    min_value=1, max_value=10, value=3
)
contrats = {}

for i in range(nb_contrats):
    cols = st.columns([2, 1])
    code = cols[0].text_input(
        f"Code financement {i+1}" if is_fr else
        f"Funding code {i+1}" if is_en else
        f"Código de financiación {i+1}",
        value=f"FH71_0{i+1}"
    )
    pct = cols[1].number_input(
        f"%" if is_fr else "%" if is_en else "%",
        min_value=0.0, max_value=100.0,
        value=round(100/nb_contrats, 2), step=1.0, key=f"pct_{i}"
    )
    if code:
        contrats[code] = pct

# Vérification total
total_pct = sum(contrats.values())
if total_pct != 100:
    st.error(
        f"❌ Le total des pourcentages est {total_pct}%. Il doit être égal à 100%." if is_fr else
        f"❌ Total percentage is {total_pct}%. It must be 100%." if is_en else
        f"❌ El porcentaje total es {total_pct}%. Debe ser igual a 100%."
    )
    st.stop()

# Génération
if st.button(
    "✅ Générer le planning" if is_fr else
    "✅ Generate timesheet" if is_en else
    "✅ Generar horario"
):
    excel_file = generer_excel(mois, annee, contrats, heures_par_jour, jours_feries)
    file_name = (
        f"planning_{mois_nom}_{annee}.xlsx" if is_fr else
        f"timesheet_{mois_nom}_{annee}.xlsx" if is_en else
        f"horario_{mois_nom}_{annee}.xlsx"
    )

    st.success(
        "Fichier Excel généré avec succès !" if is_fr else
        "Excel file generated successfully!" if is_en else
        "¡Archivo Excel generado exitosamente!"
    )
    st.download_button(
        label=(
            "📥 Télécharger le fichier Excel" if is_fr else
            "📥 Download Excel file" if is_en else
            "📥 Descargar archivo Excel"
        ),
        data=excel_file,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


