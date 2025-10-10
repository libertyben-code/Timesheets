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

def generer_excel(mois_selectionne, annee_selectionnee, contrats, heures_par_jour, jours_feries, donors=None):
    jours_mois = get_all_days(mois_selectionne, annee_selectionnee)
    jours_ouvres = get_jours_ouvres(mois_selectionne, annee_selectionnee, jours_feries)
    nb_jours_ouvres = len(jours_ouvres)
    HEURES_TOTALES = nb_jours_ouvres * heures_par_jour

    heures_cibles = {code: round(HEURES_TOTALES * pct / 100, 2) for code, pct in contrats.items()}
    contrats_list = list(contrats.keys())

    df_repartition = pd.DataFrame(index=contrats_list, columns=jours_mois, dtype=float)
    df_repartition[:] = 0.0
    heures_restantes = heures_cibles.copy()

    for jour in jours_mois:
        if jour.weekday() >= 5 or jour in jours_feries:
            df_repartition[jour] = np.nan
            continue
        max_alloc = [min(heures_restantes[code], heures_par_jour) for code in contrats_list]
        rng = np.random.default_rng()
        while True:
            props = rng.dirichlet(np.ones(len(contrats_list)))
            alloc = np.minimum(np.round(props * heures_par_jour * 2) / 2, max_alloc)
            diff = heures_par_jour - alloc.sum()
            if abs(diff) < 0.01:
                break
            idx = np.argmax(max_alloc)
            if alloc[idx] + diff <= max_alloc[idx] and alloc[idx] + diff >= 0:
                alloc[idx] += diff
                break
        for idx, code in enumerate(contrats_list):
            df_repartition.loc[code, jour] = alloc[idx]
            heures_restantes[code] -= alloc[idx]

    df_repartition.loc["Total/jour"] = df_repartition.sum(axis=0)
    df_repartition["Total contrat"] = df_repartition.sum(axis=1)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_contrats = pd.DataFrame({
            "Code financement": contrats_list,
            "Donor": [donors.get(code, "") if donors else "" for code in contrats_list],
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
    "Contrats" if is_fr else "Contracts" if is_en else "Contratos": ["FH71_01:50,FH71_02:50"],
    "Donor": ["Donor1,Donor2"]
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
        year_col = "Année" if is_fr else "Year" if is_en else "Año"
        grouped = df_upload.groupby(year_col)
        download_files = []

        for year, group in grouped:
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for idx, row in group.iterrows():
                    try:
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
                        donors = {}
                        contrats_col = "Contrats" if is_fr else "Contracts" if is_en else "Contratos"
                        donor_col = "Donor"
                        contrats_items = str(row[contrats_col]).split(",")
                        donor_items = str(row.get(donor_col, "")).split(",")
                        for i, item in enumerate(contrats_items):
                            code, pct = item.split(":")
                            contrats[code.strip()] = float(pct.strip())
                            donors[code.strip()] = donor_items[i].strip() if i < len(donor_items) else ""
                        if sum(contrats.values()) != 100:
                            continue
                        excel_file = generer_excel(mois, year, contrats, heures_par_jour, jours_feries, donors)
                        planning_df = pd.read_excel(excel_file, sheet_name="Planning", index_col=0)
                        planning_df.to_excel(writer, sheet_name=f"{calendar.month_name[mois]}")
                    except Exception as e:
                        st.warning(
                            f"Ligne {idx+1} ignorée : {e}" if is_fr else
                            f"Row {idx+1} skipped: {e}" if is_en else
                            f"Fila {idx+1} omitida: {e}"
                        )
            output.seek(0)
            download_files.append((year, output))

        st.success(
            "Tous les plannings ont été générés !" if is_fr else
            "All timesheets have been generated!" if is_en else
            "¡Todos los horarios han sido generados!"
        )

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for year, fileobj in download_files:
                filename = (
                    f"plannings_{year}.xlsx" if is_fr else
                    f"timesheets_{year}.xlsx" if is_en else
                    f"horarios_{year}.xlsx"
                )
                zipf.writestr(filename, fileobj.getvalue())
        zip_buffer.seek(0)

        st.download_button(
            label=(
                "📥 Télécharger tous les plannings (ZIP)" if is_fr else
                "📥 Download all timesheets (ZIP)" if is_en else
                "📥 Descargar todos los horarios (ZIP)"
            ),
            data=zip_buffer,
            file_name=(
                "plannings_annuels.zip" if is_fr else
                "yearly_timesheets.zip" if is_en else
                "horarios_anuales.zip"
            ),
            mime="application/zip"
        )


