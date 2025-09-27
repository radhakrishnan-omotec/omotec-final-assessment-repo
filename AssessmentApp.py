import streamlit as st
import pandas as pd
import os
import base64
import hashlib
from datetime import datetime
import logging
import sys
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
import warnings

# Suppress all warnings globally
warnings.filterwarnings('ignore')

# Configure logging for Streamlit Cloud
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="OMOTEC Mentors Assessment App", layout="wide", initial_sidebar_state="expanded")

CSV_FILE = "assessment_data.csv"
DEFAULT_DATA_FILE = "EVALUATOR_INPUT.csv"
EVALUATOR_STORE = "evaluators.csv"

# Predefined course options
COURSE_OPTIONS = [
    "", "Introduction to Coding", "Robotics Basics", "AI Fundamentals", 
    "3D Printing", "Electronics 101", "Data Analytics", 
    "Mechanical Design", "STEM Project Management", 
    "Advanced Programming", "Circuit Design"
]

CSV_COLUMNS = [
    "Trainer ID", "Trainer Name", "Department", "DOJ", "Branch", "Discipline", "Course", "Date of assessment",
    "Has Knowledge of STEM (5)", "Ability to integrate STEM With related activities (10)",
    "Discusses Up-to-date information related to STEM (5)", "Provides Course Outline (5)", "Language Fluency (5)",
    "Preparation with Lesson Plan / Practicals (5)", "Time Based Activity (5)", "Student Engagement Ideas (5)",
    "Pleasing Look (5)", "Poised & Confident (5)", "Well Modulated Voice (5)",
    "LEVEL #1 Course :1", "LEVEL #1 Course :2", "LEVEL #1 Course :3", "LEVEL #1 Course :4", "LEVEL #1 Course :5",
    "LEVEL #1 Course :6", "LEVEL #1 Course :7", "LEVEL #1 Course :8", "LEVEL #1 Course :9", "LEVEL #1 Course :10",
    "LEVEL #1 TOTAL", "LEVEL #1 AVERAGE", "LEVEL #1 STATUS", "LEVEL #1 Reminder", "LEVEL #1 Score Card Status",
    "LEVEL #2 Course :1", "LEVEL #2 Course :2", "LEVEL #2 Course :3", "LEVEL #2 Course :4", "LEVEL #2 Course :5",
    "LEVEL #2 Course :6", "LEVEL #2 Course :7", "LEVEL #2 Course :8", "LEVEL #2 Course :9", "LEVEL #2 Course :10",
    "LEVEL #2 TOTAL", "LEVEL #2 AVERAGE", "LEVEL #2 STATUS", "LEVEL #2 Reminder", "LEVEL #2 Score Card Status",
    "LEVEL #3 Course :1", "LEVEL #3 Course :2", "LEVEL #3 Course :3", "LEVEL #3 Course :4", "LEVEL #3 Course :5",
    "LEVEL #3 Course :6", "LEVEL #3 Course :7", "LEVEL #3 Course :8", "LEVEL #3 Course :9", "LEVEL #3 Course :10",
    "LEVEL #3 TOTAL", "LEVEL #3 AVERAGE", "LEVEL #3 STATUS", "LEVEL #3 Reminder", "LEVEL #3 Score Card Status",
    "LEVEL #1", "LEVEL #2", "LEVEL #3", "Evaluator Username", "Evaluator Role", "Manager Referral"
] + [f"{param} Course :{i}" for param in [
    "Has Knowledge of STEM (5)", "Ability to integrate STEM With related activities (10)",
    "Discusses Up-to-date information related to STEM (5)", "Provides Course Outline (5)", "Language Fluency (5)",
    "Preparation with Lesson Plan / Practicals (5)", "Time Based Activity (5)", "Student Engagement Ideas (5)",
    "Pleasing Look (5)", "Poised & Confident (5)", "Well Modulated Voice (5)"
] for i in range(1, 11)] + [
    f"{level} Course :{i} TOTAL" for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"] for i in range(1, 11)
] + [
    f"{level} Course :{i} AVERAGE" for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"] for i in range(1, 11)
] + [
    f"{level} Course :{i} STATUS" for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"] for i in range(1, 11)
] + [
    f"{level} Course :{i} Remarks" for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"] for i in range(1, 11)
]

EVALUATOR_COLUMNS = ["username", "password_hash", "full_name", "email", "role", "created_at"]

def hash_password(password: str) -> str:
    try:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        return ""

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return hash_password(password) == stored_hash
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

def load_data():
    try:
        if not os.path.exists(CSV_FILE):
            if os.path.exists(DEFAULT_DATA_FILE):
                df = pd.read_csv(DEFAULT_DATA_FILE)
            else:
                df = pd.DataFrame(columns=CSV_COLUMNS)
            df.to_csv(CSV_FILE, index=False)
        else:
            df = pd.read_csv(CSV_FILE)

        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[CSV_COLUMNS]
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        st.error("Failed to load assessment data. Please try again later.")
        return pd.DataFrame(columns=CSV_COLUMNS)

def generate_new_trainer_id():
    try:
        if os.path.exists(DEFAULT_DATA_FILE):
            df = pd.read_csv(DEFAULT_DATA_FILE)
            if "Trainer ID" in df.columns:
                existing_ids = df["Trainer ID"].dropna().astype(str)
                numbers = []
                for tid in existing_ids:
                    if tid.startswith("TR00"):
                        num_part = tid.replace("TR00", "")
                        if num_part.isdigit():
                            numbers.append(int(num_part))
                next_number = max(numbers) + 1 if numbers else 1
                return f"TR00{next_number}"
    except Exception as e:
        logger.error(f"Trainer ID generation failed: {str(e)}")
        st.error("Failed to generate Trainer ID. Using default ID.")
    return "TR001"

def save_new_trainer_to_input(trainer_id, trainer_name, department, trainer_email=""):
    try:
        if os.path.exists(DEFAULT_DATA_FILE):
            df = pd.read_csv(DEFAULT_DATA_FILE)
        else:
            df = pd.DataFrame(columns=["Trainer ID", "Trainer Name", "Department", "Branch", "Email"])
        
        if "Trainer ID" not in df.columns:
            df["Trainer ID"] = ""
        if "Trainer Name" not in df.columns:
            df["Trainer Name"] = ""
        if "Department" not in df.columns:
            df["Department"] = ""
        if "Branch" not in df.columns:
            df["Branch"] = ""
        if "Email" not in df.columns:
            df["Email"] = ""
            
        if trainer_id in df["Trainer ID"].values:
            idx = df.index[df["Trainer ID"] == trainer_id][0]
            df.at[idx, "Trainer Name"] = trainer_name
            df.at[idx, "Department"] = department
            df.at[idx, "Email"] = trainer_email
        else:
            new_entry = {
                "Trainer ID": trainer_id,
                "Trainer Name": trainer_name,
                "Department": department,
                "Branch": "",
                "Email": trainer_email
            }
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(DEFAULT_DATA_FILE, index=False)
        return df
    except Exception as e:
        logger.error(f"Error saving new trainer: {str(e)}")
        st.error("Failed to save new trainer information.")
        return pd.DataFrame(columns=["Trainer ID", "Trainer Name", "Department", "Branch", "Email"])

def load_evaluators():
    try:
        if not os.path.exists(EVALUATOR_STORE):
            df = pd.DataFrame(columns=EVALUATOR_COLUMNS)
            df.to_csv(EVALUATOR_STORE, index=False)
        else:
            df = pd.read_csv(EVALUATOR_STORE)
        for col in EVALUATOR_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[EVALUATOR_COLUMNS].copy()
    except Exception as e:
        logger.error(f"Error loading evaluators: {str(e)}")
        st.error("Failed to load evaluator data.")
        return pd.DataFrame(columns=EVALUATOR_COLUMNS)

def save_evaluators(df):
    try:
        df.to_csv(EVALUATOR_STORE, index=False)
    except Exception as e:
        logger.error(f"Error saving evaluators: {str(e)}")
        st.error("Failed to save evaluator data.")

def show_error_message(message, key):
    html = f"""
    <div style="position: fixed; bottom: 0; left: 0; width: 100%; background-color: #f8d7da; padding: 10px; text-align: center; z-index: 1000;" id="error_{key}">
        <p style="color: red; margin: 0; font-weight: bold; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis;">{message}</p>
        <p style="color: green; margin: 5px 0 0 0; font-weight: bold;">Proceed with your corrected data</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def evaluator_section(df_main):
    try:
        st.subheader("🧑‍🏫 Evaluator Dashboard")

        # CSS for tab animations, level heading backgrounds, score metrics, and download button styling
        st.markdown("""
        <style>
        .stTabs [role="tab"] {
            animation: slideIn 0.5s ease-in-out;
        }
        @keyframes slideIn {
            0% { transform: translateX(-20px); opacity: 0; }
            100% { transform: translateX(0); opacity: 1; }
        }
        .level-1-heading {
            background-color: #0FA753 !important;
            padding: 10px;
            border-radius: 5px;
            color: white;
        }
        .level-2-heading {
            background-color: #00A191 !important;
            padding: 10px;
            border-radius: 5px;
            color: white;
        }
        .level-3-heading {
            background-color: #8EC200 !important;
            padding: 10px;
            border-radius: 5px;
            color: white;
        }
        .score-metric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
        }
        .score-metric .stMetric > label {
            font-size: 14px;
            color: #333;
        }
        .score-metric .stMetric > div > div {
            font-size: 18px;
            color: #0FA753;
        }
        .download-section {
            background-color: #e6f3ff;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
            border: 1px solid #b3d4fc;
        }
        </style>
        """, unsafe_allow_html=True)

        if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
            st.warning("Please login to access the evaluator panel.")
            return

        df = df_main.copy()
        if "Trainer ID" not in df.columns:
            show_error_message("❌ 'Trainer ID' column missing in data.", "missing_trainer_id")
            return

        evaluator_role = st.selectbox(
            "Select Evaluator Role",
            ["Technical Evaluator", "School Operations Evaluator"],
            key="evaluator_role"
        )
        evaluator_username = st.session_state.get("logged_user", "")

        relevant_params = {
            "Technical Evaluator": [
                "Has Knowledge of STEM (5)",
                "Ability to integrate STEM With related activities (10)",
                "Discusses Up-to-date information related to STEM (5)",
                "Provides Course Outline (5)",
                "Language Fluency (5)",
                "Preparation with Lesson Plan / Practicals (5)"
            ],
            "School Operations Evaluator": [
                "Time Based Activity (5)",
                "Student Engagement Ideas (5)",
                "Pleasing Look (5)",
                "Poised & Confident (5)",
                "Well Modulated Voice (5)"
            ]
        }

        mode = st.radio("Select Trainer ID Mode", ["Enter Existing Trainer ID", "New Trainer Creation ID"])
        trainer_id, trainer_name, department, trainer_email = "", "", "", ""

        if mode.startswith("Enter"):
            try:
                if os.path.exists(DEFAULT_DATA_FILE):
                    eval_inputs_df = pd.read_csv(DEFAULT_DATA_FILE).fillna("")
                    if "Trainer ID" not in eval_inputs_df.columns:
                        show_error_message("❌ 'Trainer ID' column missing in EVALUATOR_INPUT.csv.", "missing_trainer_id_csv")
                        return
                    available_ids = [""] + eval_inputs_df["Trainer ID"].dropna().unique().tolist()
                    selected_id = st.selectbox("Select Existing Trainer ID", available_ids, index=0)
                    if selected_id:
                        trainer_data = eval_inputs_df[eval_inputs_df["Trainer ID"] == selected_id].iloc[0].to_dict()
                        trainer_id = trainer_data.get("Trainer ID", "")
                        trainer_name = trainer_data.get("Trainer Name", "")
                        department = trainer_data.get("Department", "")
                        trainer_email = trainer_data.get("Email", "")
                        st.success(f"Loaded Trainer ID: {trainer_id}")
                else:
                    show_error_message("EVALUATOR_INPUT.csv not found.", "file_not_found")
                    return
            except Exception as e:
                logger.error(f"Error loading existing trainer data: {str(e)}")
                show_error_message("Unable to load trainer data, please check the file or try again.", "load_error")
                return

            # Make details editable
            trainer_name = st.text_input("Trainer Name", value=trainer_name)
            department = st.text_input("Department", value=department)
            trainer_email = st.text_input("Trainer Email", value=trainer_email)

        # New Trainer ID or Update Existing
        else:
            trainer_id = st.text_input("Enter New Trainer ID (leave blank to auto-generate)")
            trainer_name = st.text_input("Trainer Name")
            department = st.text_input("Department")
            trainer_email = st.text_input("Trainer Email")
            if trainer_id.strip() == "":
                if trainer_name and department and trainer_email:
                    st.info("Trainer ID will be auto-generated upon submission.")
                else:
                    st.warning("Please enter Trainer Name, Department, and Email for auto-generation.")
            if st.button("SUBMISSION", key=f"submit_new_trainer_{trainer_name}"):
                try:
                    if not trainer_id and not (trainer_name and department and trainer_email):
                        show_error_message("Mandatory fields (Trainer Name, Department, Email) are missing!", "mandatory_fields_missing")
                        return
                    if not trainer_id:
                        import uuid
                        trainer_id = str(uuid.uuid4())
                    entry = {
                        "Trainer ID": trainer_id,
                        "Trainer Name": trainer_name,
                        "Department": department,
                        "Email": trainer_email
                    }
                    if os.path.exists(DEFAULT_DATA_FILE):
                        eval_inputs_df = pd.read_csv(DEFAULT_DATA_FILE)
                        if trainer_id in eval_inputs_df["Trainer ID"].values:
                            idx = eval_inputs_df.index[eval_inputs_df["Trainer ID"] == trainer_id].tolist()[0]
                            eval_inputs_df.at[idx, "Trainer Name"] = trainer_name
                            eval_inputs_df.at[idx, "Department"] = department
                            eval_inputs_df.at[idx, "Email"] = trainer_email
                        else:
                            eval_inputs_df = pd.concat([eval_inputs_df, pd.DataFrame([entry])], ignore_index=True)
                    else:
                        eval_inputs_df = pd.DataFrame([entry])
                    eval_inputs_df.to_csv(DEFAULT_DATA_FILE, index=False)
                    st.success(f"Trainer ID {trainer_id} {'updated' if trainer_id in eval_inputs_df['Trainer ID'].values else 'created'} successfully!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error creating or updating trainer: {str(e)}")
                    show_error_message("Failed to create or update trainer due to an error!", "trainer_update_error")
                    return

        # Display previous assessments
        past_assessments = df[df["Trainer ID"] == trainer_id] if trainer_id else pd.DataFrame()
        if not past_assessments.empty:
            st.markdown("### 🔁 Previous Assessments")
            st.dataframe(past_assessments, use_container_width=True)

        levels = ["LEVEL #1", "LEVEL #2", "LEVEL #3"]
        level_status, submissions, assessment_data = {}, {}, {}

        try:
            for level in levels:
                level_rows = past_assessments[past_assessments[level] == "QUALIFIED"] if not past_assessments.empty else pd.DataFrame()
                evaluators = level_rows["Evaluator Username"].tolist() if not level_rows.empty else []
                has_tech = any("technical" in s.lower() for s in level_rows["Evaluator Role"].fillna("")) if not level_rows.empty else False
                has_ops = any("school" in s.lower() for s in level_rows["Evaluator Role"].fillna("")) if not level_rows.empty else False
                if has_tech and has_ops:
                    level_status[level] = "QUALIFIED"
                else:
                    level_status[level] = "NOT QUALIFIED"
                submissions[f"{level}_submissions"] = len(set(evaluators))
        except Exception as e:
            logger.error(f"Error processing level statuses: {str(e)}")
            show_error_message("Unable to process some level statuses, continuing with available data.", "level_status_error")
            return

        level_1_qualified = all(past_assessments[f"LEVEL #1 Course :{i} STATUS"].eq("QUALIFIED").all() for i in range(1, 11)) if not past_assessments.empty and all(f"LEVEL #1 Course :{i} STATUS" in past_assessments.columns for i in range(1, 11)) else False
        level_2_qualified = all(past_assessments[f"LEVEL #2 Course :{i} STATUS"].eq("QUALIFIED").all() for i in range(1, 11)) if not past_assessments.empty and all(f"LEVEL #2 Course :{i} STATUS" in past_assessments.columns for i in range(1, 11)) else False

        for level in levels:
            level_class = f"level-{level.split('#')[1]}-heading"
            label = f'<div class="{level_class}">🔹 {level} Assessment</div>'
            if level == "LEVEL #2" and not level_1_qualified:
                label = f'<div class="{level_class}">🔹 {level} not qualified</div>'
            elif level == "LEVEL #3" and not level_2_qualified:
                label = f'<div class="{level_class}">🔹 {level} not qualified</div>'
            st.markdown(label, unsafe_allow_html=True)

            with st.expander(f"{level} Assessment"):
                try:
                    courses = {}
                    course_params = {f"Course :{i}": {} for i in range(1, 11)}
                    manager_referral = ""
                    status = "NOT QUALIFIED"

                    if level_status.get(level) == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) >= 2:
                        st.write(f"{level} already qualified by both evaluators.")
                    elif level_status.get(level) == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) == 1:
                        st.write(f"{level} qualified by one evaluator. Awaiting second evaluation.")
                    else:
                        eligible = (
                            level == "LEVEL #1" or
                            (level == "LEVEL #2" and level_1_qualified) or
                            (level == "LEVEL #3" and level_2_qualified)
                        )
                        if eligible:
                            st.markdown(f"### {level} Courses")
                            tabs = st.tabs([f"Course :{i}" for i in range(1, 11)])

                            for i, tab in enumerate(tabs, 1):
                                with tab:
                                    course_key = f"{level} Course :{i}"
                                    course_select = st.selectbox(
                                        f"{course_key} Select Course Name",
                                        options=COURSE_OPTIONS,
                                        key=f"course_select_{level}_{i}_{trainer_id}",
                                        placeholder="Select course"
                                    )

                                    if evaluator_role == "Technical Evaluator":
                                        param_has_stem = st.number_input("Has Knowledge of STEM (5)", 0, 5, key=f"stem_{level}_{i}_{trainer_id}")
                                        param_integration = st.number_input("Ability to integrate STEM With related activities (10)", 0, 10, key=f"integration_{level}_{i}_{trainer_id}")
                                        param_up_to_date = st.number_input("Discusses Up-to-date information related to STEM (5)", 0, 5, key=f"uptodate_{level}_{i}_{trainer_id}")
                                        param_outline = st.number_input("Provides Course Outline (5)", 0, 5, key=f"outline_{level}_{i}_{trainer_id}")
                                        param_language = st.number_input("Language Fluency (5)", 0, 5, key=f"language_{level}_{i}_{trainer_id}")
                                        param_preparation = st.number_input("Preparation with Lesson Plan / Practicals (5)", 0, 5, key=f"preparation_{level}_{i}_{trainer_id}")

                                        course_params[f"Course :{i}"] = {
                                            "Has Knowledge of STEM (5)": param_has_stem,
                                            "Ability to integrate STEM With related activities (10)": param_integration,
                                            "Discusses Up-to-date information related to STEM (5)": param_up_to_date,
                                            "Provides Course Outline (5)": param_outline,
                                            "Language Fluency (5)": param_language,
                                            "Preparation with Lesson Plan / Practicals (5)": param_preparation
                                        }

                                    elif evaluator_role == "School Operations Evaluator":
                                        param_time = st.number_input("Time Based Activity (5)", 0, 5, key=f"time_{level}_{i}_{trainer_id}")
                                        param_engagement = st.number_input("Student Engagement Ideas (5)", 0, 5, key=f"engagement_{level}_{i}_{trainer_id}")
                                        param_pleasing = st.number_input("Pleasing Look (5)", 0, 5, key=f"pleasing_{level}_{i}_{trainer_id}")
                                        param_poised = st.number_input("Poised & Confident (5)", 0, 5, key=f"poised_{level}_{i}_{trainer_id}")
                                        param_voice = st.number_input("Well Modulated Voice (5)", 0, 5, key=f"voice_{level}_{i}_{trainer_id}")

                                        course_params[f"Course :{i}"] = {
                                            "Time Based Activity (5)": param_time,
                                            "Student Engagement Ideas (5)": param_engagement,
                                            "Pleasing Look (5)": param_pleasing,
                                            "Poised & Confident (5)": param_poised,
                                            "Well Modulated Voice (5)": param_voice
                                        }

                                    if f"attempt_{level}_{i}_{trainer_id}" not in st.session_state:
                                        st.session_state[f"attempt_{level}_{i}_{trainer_id}"] = 1
                                    attempt = st.session_state[f"attempt_{level}_{i}_{trainer_id}"]
                                    st.info(f"Attempt: {attempt}")

                                    remarks = st.text_area("Remarks", key=f"remarks_{level}_{i}_{trainer_id}")

                                    if evaluator_role == "Technical Evaluator":
                                        if st.button(f"Calculate Score", key=f"calc_{level}_{i}_{trainer_id}"):
                                            try:
                                                if not course_select:
                                                    show_error_message("Please select a course name!", "no_course_selected_calc")
                                                    return
                                                calculated_total = (
                                                    param_has_stem + param_integration + param_up_to_date +
                                                    param_outline + param_language + param_preparation
                                                )
                                                calculated_avg = calculated_total / 6.0 if 6 > 0 else 0.0
                                                st.session_state[f"total_{level}_{i}_{trainer_id}"] = calculated_total
                                                st.session_state[f"avg_{level}_{i}_{trainer_id}"] = calculated_avg
                                                st.success(f"Calculated Total: {calculated_total}, Average: {calculated_avg:.2f}")

                                                save_new_trainer_to_input(trainer_id, trainer_name, department, trainer_email)

                                                course_entry = {
                                                    "Trainer ID": trainer_id,
                                                    "Trainer Name": trainer_name,
                                                    "Department": department,
                                                    "Date of assessment": datetime.today().date().strftime("%Y-%m-%Y"),
                                                    "Evaluator Username": evaluator_username,
                                                    "Evaluator Role": evaluator_role,
                                                    f"{course_key}": course_select,
                                                    f"{course_key} TOTAL": calculated_total,
                                                    f"{course_key} AVERAGE": calculated_avg,
                                                    f"{course_key} STATUS": st.session_state.get(f"status_{level}_{i}_{trainer_id}", "REDO"),
                                                    f"{course_key} Remarks": remarks
                                                }
                                                for param, value in course_params[f"Course :{i}"].items():
                                                    course_entry[f"{param} Course :{i}"] = value

                                                updated_df = df.copy()
                                                if trainer_id in updated_df["Trainer ID"].values:
                                                    idx = updated_df.index[updated_df["Trainer ID"] == trainer_id].tolist()[-1]
                                                    for key, value in course_entry.items():
                                                        updated_df.at[idx, key] = value
                                                else:
                                                    updated_df = pd.concat([updated_df, pd.DataFrame([course_entry])], ignore_index=True)
                                                updated_df.to_csv(CSV_FILE, index=False)

                                                st.rerun()

                                            except Exception as e:
                                                logger.error(f"Error updating data on Calculate Score: {str(e)}")
                                                show_error_message("Error calculating score, please check inputs!", "calc_score_error")
                                                return
                                    elif evaluator_role == "School Operations Evaluator":
                                        if st.button(f"Calculate Score", key=f"calc_{level}_{i}_{trainer_id}"):
                                            try:
                                                if not course_select:
                                                    show_error_message("Please select a course name!", "no_course_selected_calc")
                                                    return
                                                calculated_total = (
                                                    param_time + param_engagement + param_pleasing +
                                                    param_poised + param_voice
                                                )
                                                calculated_avg = calculated_total / 5.0 if 5 > 0 else 0.0
                                                st.session_state[f"total_{level}_{i}_{trainer_id}"] = calculated_total
                                                st.session_state[f"avg_{level}_{i}_{trainer_id}"] = calculated_avg
                                                st.success(f"Calculated Total: {calculated_total}, Average: {calculated_avg:.2f}")

                                                save_new_trainer_to_input(trainer_id, trainer_name, department, trainer_email)

                                                course_entry = {
                                                    "Trainer ID": trainer_id,
                                                    "Trainer Name": trainer_name,
                                                    "Department": department,
                                                    "Date of assessment": datetime.today().date().strftime("%Y-%m-%Y"),
                                                    "Evaluator Username": evaluator_username,
                                                    "Evaluator Role": evaluator_role,
                                                    f"{course_key}": course_select,
                                                    f"{course_key} TOTAL": calculated_total,
                                                    f"{course_key} AVERAGE": calculated_avg,
                                                    f"{course_key} STATUS": st.session_state.get(f"status_{level}_{i}_{trainer_id}", "REDO"),
                                                    f"{course_key} Remarks": remarks
                                                }
                                                for param, value in course_params[f"Course :{i}"].items():
                                                    course_entry[f"{param} Course :{i}"] = value

                                                updated_df = df.copy()
                                                if trainer_id in updated_df["Trainer ID"].values:
                                                    idx = updated_df.index[updated_df["Trainer ID"] == trainer_id].tolist()[-1]
                                                    for key, value in course_entry.items():
                                                        updated_df.at[idx, key] = value
                                                else:
                                                    updated_df = pd.concat([updated_df, pd.DataFrame([course_entry])], ignore_index=True)
                                                updated_df.to_csv(CSV_FILE, index=False)

                                                st.rerun()

                                            except Exception as e:
                                                logger.error(f"Error updating data on Calculate Score: {str(e)}")
                                                show_error_message("Error calculating score, please check inputs!", "calc_score_error")
                                                return
                                    # Updated logic: Display scores visibly below the Calculate Score button
                                    calculated_total = st.session_state.get(f"total_{level}_{i}_{trainer_id}", 0)
                                    calculated_avg = st.session_state.get(f"avg_{level}_{i}_{trainer_id}", 0.0)
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown('<div class="score-metric">', unsafe_allow_html=True)
                                        st.metric("Total Score", calculated_total, delta=None)
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    with col2:
                                        st.markdown('<div class="score-metric">', unsafe_allow_html=True)
                                        st.metric("Average Score", f"{calculated_avg:.2f}", delta=None)
                                        st.markdown('</div>', unsafe_allow_html=True)
                                    status_overall = st.selectbox(f"Course :{i} STATUS", ["CLEARED", "REDO"], key=f"status_{level}_{i}_{trainer_id}")
                                    # Enhanced logic: Increment only on change to "REDO"
                                    prev_status_key = f"prev_status_{level}_{i}_{trainer_id}"
                                    current_status = status_overall
                                    prev_status = st.session_state.get(prev_status_key, "CLEARED")
                                    if current_status == "REDO" and prev_status != "REDO":
                                        st.session_state[f"attempt_{level}_{i}_{trainer_id}"] += 1
                                    st.session_state[prev_status_key] = current_status
                                    course_passed = st.checkbox(f"{course_key} Passed", key=f"course_pass_{level}_{i}_{trainer_id}")

                                    final_course = course_select
                                    courses[course_key] = {
                                        "name": final_course,
                                        "passed": course_passed,
                                        "total": calculated_total,
                                        "average": calculated_avg,
                                        "status_overall": status_overall,
                                        "params": course_params[f"Course :{i}"],
                                        "remarks": remarks
                                    }
                                    st.session_state[f"course_passed_{level}_{i}_{trainer_id}"] = course_passed

                            # Enhanced: Compute cleared status per course (name selected + passed + min average)
                            min_avg_threshold = 75.0 if level in ["LEVEL #1", "LEVEL #2"] else 90.0
                            all_courses_cleared = True
                            for i in range(1, 11):
                                course_data = courses.get(f"{level} Course :{i}", {})
                                course_name = course_data.get("name", "")
                                course_passed = course_data.get("passed", False)
                                course_avg = course_data.get("average", 0.0)
                                if not (course_name and course_passed and course_avg >= min_avg_threshold):
                                    all_courses_cleared = False
                                    break

                            # Use cleared status for both filled and passed checks
                            all_courses_filled = all_courses_cleared
                            all_courses_passed = all_courses_cleared

                            # Status selectbox: Default to NOT QUALIFIED; restrict QUALIFIED until cleared
                            level_status_key = f"{level}_status_{evaluator_role}"
                            status_options = ["QUALIFIED", "NOT QUALIFIED"]
                            default_status_index = 0 if all_courses_cleared else 1
                            if all_courses_cleared:
                                status = st.selectbox(
                                    f"{level} Status",
                                    status_options,
                                    index=default_status_index,
                                    key=level_status_key
                                )
                            else:
                                status = st.selectbox(
                                    f"{level} Status",
                                    ["NOT QUALIFIED"],
                                    index=0,
                                    key=level_status_key
                                )
                                st.warning(f"🔒 {level} Status locked to 'NOT QUALIFIED' until all 10 courses are cleared (name selected, passed, and average ≥ {min_avg_threshold}%).")

                            # Progress metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Courses Filled", sum(1 for i in range(1, 11) if courses.get(f"{level} Course :{i}", {}).get("name")), delta=10 - sum(1 for i in range(1, 11) if courses.get(f"{level} Course :{i}", {}).get("name")))
                            with col2:
                                st.metric("Courses Passed", sum(1 for i in range(1, 11) if st.session_state.get(f"course_passed_{level}_{i}_{trainer_id}", False)), delta=10 - sum(1 for i in range(1, 11) if st.session_state.get(f"course_passed_{level}_{i}_{trainer_id}", False)))
                            with col3:
                                cleared_count = sum(1 for i in range(1, 11) if courses.get(f"{level} Course :{i}", {}).get("average", 0) >= min_avg_threshold)
                                st.metric("Courses Scored ≥ Threshold", cleared_count, delta=10 - cleared_count)
                                if cleared_count == 10 and all_courses_cleared:
                                    st.success(f"✅ {level} is now eligible for QUALIFIED!")

                            if level == "LEVEL #3":
                                manager_referral = st.text_input(
                                    "Manager Referral (Required for Level 3)",
                                    key=f"manager_referral_{level}_{trainer_id}"
                                )

                            # Place "Save Assessment in DB" and "Download Assessment CSV Report" side by side
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Save Assessment in Report", key=f"save_{level}_{trainer_id}"):
                                    try:
                                        entry = {
                                            "Trainer ID": trainer_id,
                                            "Trainer Name": trainer_name,
                                            "Department": department,
                                            "Date of assessment": datetime.today().date().strftime("%Y-%m-%Y"),
                                            "Evaluator Username": evaluator_username,
                                            "Evaluator Role": evaluator_role
                                        }
                                        for i in range(1, 11):
                                            course_key = f"{level} Course :{i}"
                                            course_data = courses.get(course_key, {})
                                            entry[course_key] = course_data.get("name", "")
                                            entry[f"{course_key} TOTAL"] = float(course_data.get("total", 0))  # Ensure float type
                                            entry[f"{course_key} AVERAGE"] = float(course_data.get("average", 0.0))  # Ensure float type
                                            entry[f"{course_key} STATUS"] = course_data.get("status_overall", "REDO")
                                            entry[f"{course_key} Remarks"] = course_data.get("remarks", "")
                                            for param in relevant_params[evaluator_role]:
                                                entry[f"{param} Course :{i}"] = float(course_data.get("params", {}).get(param, 0))  # Ensure float type for numeric params

                                        # Update EVALUATOR_INPUT.csv with all columns
                                        if os.path.exists(DEFAULT_DATA_FILE):
                                            eval_inputs_df = pd.read_csv(DEFAULT_DATA_FILE)
                                            if trainer_id in eval_inputs_df["Trainer ID"].values:
                                                idx = eval_inputs_df.index[eval_inputs_df["Trainer ID"] == trainer_id].tolist()[0]
                                                for key, value in entry.items():
                                                    if key not in eval_inputs_df.columns:
                                                        eval_inputs_df.insert(eval_inputs_df.columns.get_loc("Date of assessment") + 1, key, "No data entered" if isinstance(value, str) else 0)
                                                    eval_inputs_df.at[idx, key] = value
                                            else:
                                                new_row = pd.DataFrame([entry])
                                                for col in eval_inputs_df.columns:
                                                    if col not in new_row.columns:
                                                        new_row[col] = "No data entered" if eval_inputs_df[col].dtype == 'object' else 0
                                                for col in new_row.columns:
                                                    if col not in eval_inputs_df.columns:
                                                        eval_inputs_df.insert(eval_inputs_df.columns.get_loc("Date of assessment") + 1, col, "No data entered" if new_row[col].dtype == 'object' else 0)
                                                eval_inputs_df = pd.concat([eval_inputs_df, new_row], ignore_index=True)
                                            eval_inputs_df.to_csv(DEFAULT_DATA_FILE, index=False, float_format='%.2f')  # Ensure consistent float formatting
                                        else:
                                            new_df = pd.DataFrame([entry])
                                            for col in new_df.columns:
                                                if col not in ["Trainer ID", "Trainer Name", "Department", "Email", "Date of assessment"]:
                                                    new_df[col] = "No data entered" if new_df[col].dtype == 'object' else 0
                                            new_df.to_csv(DEFAULT_DATA_FILE, index=False, float_format='%.2f')  # Ensure consistent float formatting

                                        updated_df = df.copy()
                                        if os.path.exists(CSV_FILE):
                                            existing_df = pd.read_csv(CSV_FILE)
                                            match = existing_df[(existing_df["Trainer ID"] == trainer_id) & (existing_df["Department"] == department)]
                                            if not match.empty:
                                                idx = match.index[0]
                                                for key, value in entry.items():
                                                    if key in existing_df.columns:
                                                        existing_df.at[idx, key] = value
                                                    else:
                                                        existing_df.insert(existing_df.columns.get_loc("Date of assessment") + 1, key, "No data entered" if isinstance(value, str) else 0)
                                                        existing_df.at[idx, key] = value
                                                updated_df = existing_df
                                            else:
                                                updated_df = pd.concat([existing_df, pd.DataFrame([entry])], ignore_index=True)
                                                for col in updated_df.columns:
                                                    if col not in entry:
                                                        updated_df[col] = "No data entered" if updated_df[col].dtype == 'object' else 0
                                        else:
                                            updated_df = pd.DataFrame([entry])
                                            for col in updated_df.columns:
                                                if col not in entry:
                                                    updated_df[col] = "No data entered" if updated_df[col].dtype == 'object' else 0
                                        updated_df = updated_df.astype({col: float for col in updated_df.select_dtypes(include=['object']).columns if col.endswith('TOTAL') or col.endswith('AVERAGE')})
                                        updated_df.to_csv(CSV_FILE, index=False, float_format='%.2f')  # Ensure consistent float formatting
                                        st.success("Assessment saved to DB.")
                                        st.rerun()
                                    except Exception as e:
                                        logger.error(f"Error saving assessment: {str(e)}")
                                        show_error_message("Failed to save assessment due to an error!", "save_assessment_error")
                                        return

                            with col2:
                                if trainer_id:
                                    if st.button("Download Assessment CSV Report", key=f"download_all_assessed_{trainer_id}_{level}"):
                                        try:
                                            if os.path.exists(CSV_FILE):
                                                assessed_df = pd.read_csv(CSV_FILE)
                                                trainer_assessments = assessed_df[assessed_df["Trainer ID"] == trainer_id]
                                                if not trainer_assessments.empty:
                                                    csv_data = trainer_assessments.to_csv(index=False)
                                                    st.download_button(
                                                        label="Download All Assessed Data CSV",
                                                        data=csv_data,
                                                        file_name=f"all_assessments_{trainer_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                                                        mime="text/csv",
                                                        key=f"download_all_assessed_csv_{trainer_id}_{level}"
                                                    )
                                                    st.success(f"Downloaded all assessments for Trainer ID: {trainer_id}")
                                                else:
                                                    show_error_message(f"No assessment data found for Trainer ID: {trainer_id}", "no_assessed_data")
                                            else:
                                                show_error_message("Assessment data file not found.", "assessed_file_not_found")
                                        except Exception as e:
                                            logger.error(f"Error downloading assessed data: {str(e)}")
                                            show_error_message("Failed to download assessed data!", "download_assessed_error")

                            reminder = st.text_area("Reminder", key=f"reminder_{level}_{trainer_id}")
                            reminder_email = st.text_input("Reminder Email", key=f"reminder_email_{level}_{trainer_id}")

                            if st.button("Prepare Reminder Email", key=f"prepare_reminder_{level}_{trainer_id}"):
                                try:
                                    if not reminder_email:
                                        show_error_message("Please enter a reminder email!", "no_reminder_email")
                                        return
                                    st.session_state[f"prepared_email_{level}_{trainer_id}"] = reminder_email
                                    st.success(f"Reminder email prepared for {reminder_email}")
                                except Exception as e:
                                    logger.error(f"Error preparing reminder email: {str(e)}")
                                    show_error_message("Failed to prepare reminder email!", "prepare_email_error")
                                    return

                            if st.button("Open to send mail", key=f"open_mail_{level}_{trainer_id}"):
                                try:
                                    if not reminder_email:
                                        show_error_message("Please enter a reminder email!", "no_reminder_email_send")
                                        return
                                    import webbrowser
                                    subject = f"Reminder for {level}"
                                    body = reminder if reminder else ""
                                    mailto_link = f"mailto:{reminder_email}?subject={subject}&body={body}"
                                    webbrowser.open(mailto_link)
                                    st.success("Gmail mailbox opened for sending email.")
                                except Exception as e:
                                    logger.error(f"Error opening mail: {str(e)}")
                                    show_error_message("Failed to open mail client!", "open_mail_error")
                                    return

                            if st.button("Submit Evaluation", key=f"submit_{level}_{trainer_id}"):
                                try:
                                    # Final validation for required fields
                                    missing_fields = []
                                    for i in range(1, 11):
                                        course_data = courses.get(f"Course :{i}", {})
                                        if not course_data.get("name"):
                                            missing_fields.append(f"Course :{i} name")
                                        for param in relevant_params[evaluator_role]:
                                            if course_data.get("params", {}).get(param, 0) == 0:
                                                missing_fields.append(f"Course :{i} {param}")
                                        if not course_data.get("remarks"):
                                            missing_fields.append(f"Course :{i} remarks")
                                    if level == "LEVEL #3" and not manager_referral:
                                        missing_fields.append("Manager Referral")

                                    if missing_fields:
                                        st.warning("Missing required fields: " + ", ".join(missing_fields))
                                        status = "NOT QUALIFIED"

                                    if not all_courses_cleared or (level == "LEVEL #3" and not manager_referral):
                                        st.warning(f"All 10 courses must be cleared (name, passed, avg ≥ {min_avg_threshold}%) and Manager Referral required for Level 3!")
                                        status = "NOT QUALIFIED"

                                    entry = {
                                        "Trainer ID": trainer_id,
                                        "Trainer Name": trainer_name,
                                        "Department": department,
                                        "Date of assessment": datetime.today().date().strftime("%Y-%m-%Y"),
                                        "Evaluator Username": evaluator_username,
                                        "Evaluator Role": evaluator_role,
                                        f"{level}": status,
                                        f"{level} Reminder": reminder,
                                        "Manager Referral": manager_referral if level == "LEVEL #3" else ""
                                    }

                                    total_score = 0
                                    param_count = len(relevant_params[evaluator_role])
                                    for i in range(1, 11):
                                        course_key = f"{level} Course :{i}"
                                        course_data = courses.get(course_key, {})
                                        entry[course_key] = course_data.get("name", "")
                                        entry[f"{course_key} TOTAL"] = float(course_data.get("total", 0))  # Ensure float type
                                        entry[f"{course_key} AVERAGE"] = float(course_data.get("average", 0.0))  # Ensure float type
                                        entry[f"{course_key} STATUS"] = course_data.get("status_overall", "REDO")
                                        entry[f"{course_key} Remarks"] = course_data.get("remarks", "")
                                        for param in relevant_params[evaluator_role]:
                                            entry[f"{param} Course :{i}"] = float(course_data.get("params", {}).get(param, 0))  # Ensure float type for numeric params
                                        total_score += course_data.get("total", 0)
                                    entry[f"{level} TOTAL"] = float(total_score)  # Ensure float type
                                    entry[f"{level} AVERAGE"] = float(total_score / (param_count * 10) if param_count * 10 > 0 else 0.0)  # Ensure float type

                                    for lvl in levels:
                                        all_courses_filled = all(courses.get(f"{lvl} Course :{i}", {}).get("name") and courses.get(f"{lvl} Course :{i}", {}).get("passed") for i in range(1, 11))
                                        if lvl in ["LEVEL #1", "LEVEL #2"] and entry.get(lvl) == "QUALIFIED" and submissions.get(f"{lvl}_submissions", 0) >= 2:
                                            if not all_courses_filled or entry.get(f"{lvl} AVERAGE", 0.0) < 75.0:
                                                entry[lvl] = "NOT QUALIFIED"
                                                st.warning(f"{lvl} requires 10 completed courses with at least 75% average.")
                                        if lvl == "LEVEL #3" and entry.get(lvl) == "QUALIFIED" and submissions.get(f"{lvl}_submissions", 0) >= 2:
                                            if not all_courses_filled or entry.get(f"{lvl} AVERAGE", 0.0) < 90.0 or not entry.get("Manager Referral"):
                                                entry[lvl] = "NOT QUALIFIED"
                                                st.warning(f"{lvl} requires 10 completed courses, 90% average, and Manager Referral.")

                                    if not all_courses_cleared:
                                        entry[f"{level}"] = "NOT QUALIFIED"
                                        st.warning(f"{level} auto-set to NOT QUALIFIED due to incomplete clearance.")

                                    updated_df = df.copy()
                                    if os.path.exists(CSV_FILE):
                                        existing_df = pd.read_csv(CSV_FILE)
                                        match = existing_df[(existing_df["Trainer ID"] == trainer_id) & (existing_df["Department"] == department)]
                                        if not match.empty:
                                            idx = match.index[0]
                                            for key, value in entry.items():
                                                if key in existing_df.columns:
                                                    existing_df.at[idx, key] = value
                                                else:
                                                    existing_df.insert(existing_df.columns.get_loc("Date of assessment") + 1, key, "No data entered" if isinstance(value, str) else 0)
                                                    existing_df.at[idx, key] = value
                                            updated_df = existing_df
                                        else:
                                            updated_df = pd.concat([existing_df, pd.DataFrame([entry])], ignore_index=True)
                                            for col in updated_df.columns:
                                                if col not in entry:
                                                    updated_df[col] = "No data entered" if updated_df[col].dtype == 'object' else 0
                                    else:
                                        updated_df = pd.DataFrame([entry])
                                        for col in updated_df.columns:
                                            if col not in entry:
                                                updated_df[col] = "No data entered" if updated_df[col].dtype == 'object' else 0
                                    updated_df = updated_df.astype({col: float for col in updated_df.select_dtypes(include=['object']).columns if col.endswith('TOTAL') or col.endswith('AVERAGE')})
                                    updated_df.to_csv(CSV_FILE, index=False, float_format='%.2f')  # Ensure consistent float formatting

                                    st.success(f"✅ Assessment Saved for Trainer ID: {trainer_id}")
                                    st.write(f"Level Total: {entry[f'{level} TOTAL']}, Level Average: {entry[f'{level} AVERAGE']:.2f}")

                                    # Enhanced Download Submitted Assessment section
                                    with st.container():
                                        st.markdown('<div class="download-section">', unsafe_allow_html=True)
                                        st.markdown("### 📥 Download Submitted Assessment")
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            csv_data = pd.DataFrame([entry]).to_csv(index=False)
                                            st.download_button(
                                                label="Download Assessment CSV",
                                                data=csv_data,
                                                file_name=f"assessment_{trainer_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                                                mime="text/csv",
                                                key=f"download_button_eval_csv_{trainer_id}_{level}"
                                            )
                                        with col2:
                                            try:
                                                buffer = BytesIO()
                                                pdf = canvas.Canvas(buffer, pagesize=A4)
                                                pdf.setFont("Helvetica-Bold", 14)
                                                y = 750
                                                pdf.drawString(100, y, f"OMOTEC Mentors Assessment Report")
                                                pdf.setFont("Helvetica", 12)
                                                y -= 20
                                                pdf.drawString(100, y, f"Trainer ID: {trainer_id}")
                                                y -= 20
                                                pdf.drawString(100, y, f"Trainer Name: {trainer_name}")
                                                y -= 20
                                                pdf.drawString(100, y, f"Department: {department}")
                                                y -= 20
                                                pdf.drawString(100, y, f"Evaluator: {evaluator_username} ({evaluator_role})")
                                                y -= 20
                                                pdf.drawString(100, y, f"Date: {datetime.today().date().strftime('%Y-%m-%d')}")
                                                y -= 30
                                                pdf.setFont("Helvetica-Bold", 12)
                                                pdf.drawString(100, y, f"{level} Assessment")
                                                pdf.setFont("Helvetica", 12)
                                                y -= 20
                                                pdf.drawString(100, y, f"Status: {entry.get(level, 'N/A')}")
                                                y -= 20
                                                pdf.drawString(100, y, f"Total Score: {entry.get(f'{level} TOTAL', 'N/A')}")
                                                y -= 20
                                                pdf.drawString(100, y, f"Average Score: {entry.get(f'{level} AVERAGE', 'N/A'):.2f}")
                                                y -= 20
                                                pdf.drawString(100, y, f"Reminder: {entry.get(f'{level} Reminder', 'N/A')}")
                                                y -= 20
                                                if level == "LEVEL #3":
                                                    pdf.drawString(100, y, f"Manager Referral: {entry.get('Manager Referral', 'N/A')}")
                                                    y -= 20
                                                y -= 20
                                                pdf.setFont("Helvetica-Bold", 12)
                                                pdf.drawString(100, y, "Course Details")
                                                pdf.setFont("Helvetica", 12)
                                                y -= 20
                                                for i in range(1, 11):
                                                    pdf.drawString(100, y, f"Course :{i}: {entry.get(f'{level} Course :{i}', 'N/A')}")
                                                    y -= 20
                                                    for param in relevant_params[evaluator_role]:
                                                        pdf.drawString(120, y, f"{param}: {entry.get(f'{param} Course :{i}', 'N/A')}")
                                                        y -= 15
                                                    pdf.drawString(120, y, f"TOTAL: {entry.get(f'{level} Course :{i} TOTAL', 'N/A')}")
                                                    y -= 15
                                                    pdf.drawString(120, y, f"AVERAGE: {entry.get(f'{level} Course :{i} AVERAGE', 'N/A'):.2f}")
                                                    y -= 15
                                                    pdf.drawString(120, y, f"STATUS: {entry.get(f'{level} Course :{i} STATUS', 'N/A')}")
                                                    y -= 15
                                                    pdf.drawString(120, y, f"Evaluator Remarks: {entry.get(f'{level} Course :{i} Remarks', 'N/A')}")
                                                    y -= 20
                                                    if y < 50:
                                                        pdf.showPage()
                                                        pdf.setFont("Helvetica", 12)
                                                        y = 750
                                                pdf.showPage()
                                                pdf.save()
                                                pdf_data = buffer.getvalue()
                                                buffer.close()
                                                st.download_button(
                                                    label="Download Assessment PDF",
                                                    data=pdf_data,
                                                    file_name=f"assessment_{trainer_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                                    mime="application/pdf",
                                                    key=f"download_button_eval_pdf_{trainer_id}_{level}"
                                                )
                                            except Exception as e:
                                                logger.error(f"Error generating PDF: {str(e)}")
                                                show_error_message("Failed to generate PDF report!", "pdf_gen_error")
                                                return
                                        st.markdown('</div>', unsafe_allow_html=True)

                                    st.rerun()

                                except Exception as e:
                                    logger.error(f"Error submitting evaluation: {str(e)}")
                                    show_error_message("Failed to submit evaluation!", "submit_eval_final_error")
                                    return
                except Exception as e:
                    logger.error(f"Error in assessment section: {str(e)}")
                    show_error_message("Error processing assessment data!", "assessment_section_error")
                    return
        if st.button("View All Trainers", key="view_all_trainers"):
            try:
                if os.path.exists(DEFAULT_DATA_FILE):
                    all_trainers = pd.read_csv(DEFAULT_DATA_FILE)[["Trainer ID", "Trainer Name", "Department", "Branch"]].drop_duplicates()
                    st.markdown("### 🆔 All Trainers")
                    st.dataframe(all_trainers, use_container_width=True)
                else:
                    show_error_message("EVALUATOR_INPUT.csv not found.", "view_trainers_file_not_found")
                    return
            except Exception as e:
                logger.error(f"Error viewing all trainers: {str(e)}")
                show_error_message("Failed to display trainer list!", "view_trainers_error")
                return

        if st.button("Logout", key="evaluator_logout"):
            try:
                for key in ["logged_in", "role", "logged_user"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Logged out successfully!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
                show_error_message("Failed to logout!", "logout_error")
                return
    except Exception as e:
        logger.error(f"Error in evaluator section: {str(e)}")
        show_error_message("Unable to process the dashboard, please try again!", "dashboard_error")
        if st.button("Logout", key="evaluator_logout_exception"):
            try:
                for key in ["logged_in", "role", "logged_user"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Logged out successfully!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
                show_error_message("Failed to logout!", "logout_exception_error")
                return
                                                   
def viewer_section(df_main):
    try:
        st.subheader("👀 Viewer Dashboard")
        if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
            if not st.session_state.get("popup_dismissed_viewer_login_required"):
                st.session_state["popup_dismissed_viewer_login_required"] = True
                show_error_message("Please login to access the viewer panel.", "viewer_login_required")
            return

        df = df_main.copy()
        if "Trainer ID" not in df.columns:
            if not st.session_state.get("popup_dismissed_viewer_trainer_id_missing"):
                st.session_state["popup_dismissed_viewer_trainer_id_missing"] = True
                show_error_message("❌ 'Trainer ID' column missing in data.", "viewer_trainer_id_missing")
            return

        st.markdown("### 📋 Trainer Assessments")
        trainer_filter = st.text_input("Filter by Trainer Name or ID", "", help="Press Enter to Apply")

        filtered = df.copy()
        if trainer_filter:
            try:
                mask = filtered["Trainer ID"].astype(str).str.contains(trainer_filter, case=False, na=False) | \
                       filtered["Trainer Name"].astype(str).str.contains(trainer_filter, case=False, na=False)
                filtered = filtered[mask]
            except Exception as e:
                logger.error(f"Error filtering trainers: {str(e)}")
                if not st.session_state.get("popup_dismissed_trainer_filter_error"):
                    st.session_state["popup_dismissed_trainer_filter_error"] = True
                    show_error_message("Failed to apply trainer filter.", "trainer_filter_error")
                return

        if not filtered.empty:
            st.markdown("#### Matching Trainer Assessments")
            st.dataframe(filtered.fillna("No data entered"), use_container_width=True)

        trainer_ids = sorted(filtered["Trainer ID"].dropna().unique().tolist())
        selected_trainer = st.selectbox("Select Trainer for Detailed Report", [""] + trainer_ids)
        if selected_trainer:
            trainer_report = df[df["Trainer ID"] == selected_trainer]
            if trainer_report.empty:
                st.info("No data entered for this trainer.")
            else:
                st.markdown(f"##### Reports for Trainer ID: {selected_trainer}")
                st.dataframe(trainer_report.fillna("No data entered"))

            col1, col2 = st.columns(2)
            with col1:
                csv_data = trainer_report.fillna("No data entered").to_csv(index=False)
                st.download_button(
                    label="Download Trainer Report CSV",
                    data=csv_data,
                    file_name=f"trainer_{selected_trainer}_reports.csv",
                    mime="text/csv",
                    key=f"download_button_trainer_csv_{selected_trainer}"
                )
            with col2:
                try:
                    buffer = BytesIO()
                    pdf = canvas.Canvas(buffer, pagesize=A4)
                    pdf.setFont("Helvetica", 12)
                    y = 750
                    pdf.drawString(100, y, f"Trainer Report: {selected_trainer}")
                    y -= 20
                    pdf.drawString(100, y, f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M %p IST')}")
                    y -= 30
                    for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"]:
                        pdf.drawString(100, y, f"{level} Assessment")
                        y -= 20
                        for i in range(1, 11):
                            course = trainer_report.iloc[-1].get(f"{level} Course :{i}", "N/A") if not trainer_report.empty else "N/A"
                            pdf.drawString(100, y, f"Course :{i}: {course}")
                            y -= 20
                            if y < 50:
                                pdf.showPage()
                                pdf.setFont("Helvetica", 12)
                                y = 750
                    pdf.showPage()
                    pdf.save()
                    pdf_data = buffer.getvalue()
                    buffer.close()
                    st.download_button(
                        label="Download Trainer PDF",
                        data=pdf_data,
                        file_name=f"trainer_{selected_trainer}_assessment.pdf",
                        mime="application/pdf",
                        key=f"download_button_pdf_{selected_trainer}"
                    )
                except Exception as e:
                    logger.error(f"Error generating PDF: {str(e)}")
                    if not st.session_state.get("popup_dismissed_pdf_gen_error"):
                        st.session_state["popup_dismissed_pdf_gen_error"] = True
                        show_error_message("Failed to generate PDF report.", "pdf_gen_error")
                    return

        if st.button("View All Trainers", key="view_all_trainers"):
            try:
                if os.path.exists(DEFAULT_DATA_FILE):
                    # Reload the latest EVALUATOR_INPUT.csv
                    all_trainers = pd.read_csv(DEFAULT_DATA_FILE)
                    # Select relevant columns and remove duplicates
                    all_trainers = all_trainers[["Trainer ID", "Trainer Name", "Department", "Branch"]].drop_duplicates()
                    st.markdown("### 🆔 All Trainers")
                    st.dataframe(all_trainers.fillna("No data entered"), use_container_width=True)
                    # Reset popup dismissal flag after successful load
                    if "popup_dismissed_view_trainers_error" in st.session_state:
                        del st.session_state["popup_dismissed_view_trainers_error"]
                    if "popup_dismissed_viewer_trainers_file_not_found" in st.session_state:
                        del st.session_state["popup_dismissed_viewer_trainers_file_not_found"]
                else:
                    if not st.session_state.get("popup_dismissed_viewer_trainers_file_not_found"):
                        st.session_state["popup_dismissed_viewer_trainers_file_not_found"] = True
                        show_error_message("EVALUATOR_INPUT.csv not found.", "viewer_trainers_file_not_found")
                    return
            except Exception as e:
                logger.error(f"Error viewing all trainers: {str(e)}")
                if not st.session_state.get("popup_dismissed_view_trainers_error"):
                    st.session_state["popup_dismissed_view_trainers_error"] = True
                    show_error_message("Failed to display trainer list.", "view_trainers_error")
                return

        if st.button("Logout", key="viewer_logout"):
            try:
                for key in ["logged_in", "role", "logged_user"]:
                    if st.session_state.get(key):
                        del st.session_state[key]
                st.success("Logged out successfully!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
                if not st.session_state.get("popup_dismissed_viewer_logout_error"):
                    st.session_state["popup_dismissed_viewer_logout_error"] = True
                    show_error_message("Failed to logout. Please try again.", "viewer_logout_error")
                return
    except Exception as e:
        logger.error(f"Error in viewer section: {str(e)}")
        if not st.session_state.get("popup_dismissed_viewer_dashboard_error"):
            st.session_state["popup_dismissed_viewer_dashboard_error"] = True
            show_error_message("An unexpected error occurred in the Viewer Dashboard.", "viewer_dashboard_error")
        return

def admin_section(df_main):
    try:
        st.subheader("👨‍💼 Super Administrator Section")
        if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
            if not st.session_state.get("popup_dismissed_admin_login_required"):
                st.session_state["popup_dismissed_admin_login_required"] = True
                show_error_message("Please login to access the admin panel.", "admin_login_required")
            return
        evaluators_df = load_evaluators()
        st.markdown("### 🧑‍💻 Existing Evaluators")
        try:
            if not evaluators_df.empty:
                st.dataframe(evaluators_df[["username", "full_name", "email", "role", "created_at"]], use_container_width=True)
            else:
                st.info("No evaluators found in the system.")
        except Exception as e:
            logger.error(f"Error displaying evaluators list: {str(e)}")
            if not st.session_state.get("popup_dismissed_evaluators_list_error"):
                st.session_state["popup_dismissed_evaluators_list_error"] = True
                show_error_message("Failed to display evaluators list.", "evaluators_list_error")
            return
        cols = st.columns([1, 1, 1, 1])
        if cols[0].button("Add New Evaluator"):
            st.session_state.admin_section = "add_evaluator"
        if cols[1].button("Existing Evaluators"):
            st.session_state.admin_section = "existing_evaluators"
        if cols[2].button("Edit Evaluator"):
            st.session_state.admin_section = "edit_evaluator"
        if cols[3].button("Delete Evaluator"):
            st.session_state.admin_section = "delete_evaluator"
        section = st.session_state.get("admin_section", "trainer_reports")
        evaluators_df = load_evaluators()
        if section == "add_evaluator":
            st.markdown("### 🧑‍💻 Add New Evaluator")
            with st.form("add_eval_form", clear_on_submit=True):
                new_username = st.text_input("Username", key="new_eval_user")
                new_password = st.text_input("Password", type="password", key="new_eval_pass")
                confirm_password = st.text_input("Confirm Password", type="password", key="new_eval_confirm_pass")
                full_name = st.text_input("Full Name", key="new_eval_name")
                email = st.text_input("Email", key="new_eval_email")
                role_select = st.selectbox("Role", ["Technical Evaluator", "School Operations Evaluator"], key="new_eval_role")
                submitted = st.form_submit_button("Add Evaluator")
                if submitted:
                    try:
                        if not new_username or not new_password:
                            st.error("Username and password are required.")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match.")
                        elif new_username in evaluators_df["username"].values:
                            st.error("Username already exists.")
                        else:
                            new_entry = {
                                "username": new_username,
                                "password_hash": hash_password(new_password),
                                "full_name": full_name,
                                "email": email,
                                "role": role_select,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            evaluators_df = pd.concat([evaluators_df, pd.DataFrame([new_entry])], ignore_index=True)
                            save_evaluators(evaluators_df)
                            st.success(f"Evaluator '{new_username}' added.")
                            st.session_state.admin_section = "trainer_reports"
                    except Exception as e:
                        logger.error(f"Error adding evaluator: {str(e)}")
                        if not st.session_state.get("popup_dismissed_add_evaluator_error"):
                            st.session_state["popup_dismissed_add_evaluator_error"] = True
                            show_error_message("Failed to add new evaluator.", "add_evaluator_error")
        elif section == "existing_evaluators":
            st.markdown("### 🧑‍💻 Existing Evaluators")
            try:
                st.dataframe(evaluators_df[["username", "full_name", "email", "role", "created_at"]])
                # Single-click mechanism for Back to Main
                if st.button("Back to Main", key="back_to_main_existing"):
                    try:
                        if df_main is None or df_main.empty:
                            raise ValueError("Trainer reports data is missing or empty.")
                        st.session_state.admin_section = "trainer_reports"
                    except Exception as e:
                        logger.error(f"Error navigating to trainer reports: {str(e)}")
                        if not st.session_state.get("popup_dismissed_back_to_main_existing_error"):
                            st.session_state["popup_dismissed_back_to_main_existing_error"] = True
                            show_error_message("Failed to navigate to trainer reports.", "back_to_main_existing_error")
            except Exception as e:
                logger.error(f"Error displaying evaluators: {str(e)}")
                if not st.session_state.get("popup_dismissed_evaluators_list_error"):
                    st.session_state["popup_dismissed_evaluators_list_error"] = True
                    show_error_message("Failed to display evaluators list.", "evaluators_list_error")
        elif section == "edit_evaluator":
            st.markdown("### 🧑‍💻 Edit Evaluator")
            selected_eval = st.selectbox("Select Evaluator to Edit", [""] + evaluators_df["username"].tolist(), key="select_eval_edit")
            if selected_eval:
                try:
                    row = evaluators_df[evaluators_df["username"] == selected_eval].iloc[0].to_dict()
                    with st.form(f"edit_eval_form_{selected_eval}"):
                        st.markdown(f"**Username:** {row['username']} (immutable)")
                        edit_full_name = st.text_input("Full Name", value=row.get("full_name", ""), key=f"name_{selected_eval}")
                        edit_email = st.text_input("Email", value=row.get("email", ""), key=f"email_{selected_eval}")
                        edit_role = st.selectbox("Role", ["Technical Evaluator", "School Operations Evaluator"],
                                                 index=["Technical Evaluator", "School Operations Evaluator"].index(row.get("role", "Technical Evaluator")),
                                                 key=f"role_{selected_eval}")
                        change_password = st.checkbox("Change Password", key=f"chpass_{selected_eval}")
                        new_pass = ""
                        confirm_pass = ""
                        if change_password:
                            new_pass = st.text_input("New Password", type="password", key=f"newpass_{selected_eval}")
                            confirm_pass = st.text_input("Confirm New Password", type="password", key=f"confirmpass_{selected_eval}")
                        edit_submitted = st.form_submit_button("Save Changes")
                        if edit_submitted:
                            try:
                                if change_password and new_pass != confirm_pass:
                                    st.error("Passwords do not match.")
                                else:
                                    idx = evaluators_df.index[evaluators_df["username"] == selected_eval][0]
                                    evaluators_df.at[idx, "full_name"] = edit_full_name
                                    evaluators_df.at[idx, "email"] = edit_email
                                    evaluators_df.at[idx, "role"] = edit_role
                                    if change_password and new_pass:
                                        evaluators_df.at[idx, "password_hash"] = hash_password(new_pass)
                                    save_evaluators(evaluators_df)
                                    st.success(f"Evaluator '{selected_eval}' updated.")
                            except Exception as e:
                                logger.error(f"Error editing evaluator: {str(e)}")
                                if not st.session_state.get("popup_dismissed_edit_evaluator_error"):
                                    st.session_state["popup_dismissed_edit_evaluator_error"] = True
                                    show_error_message("Failed to edit evaluator.", "edit_evaluator_error")
                except Exception as e:
                    logger.error(f"Error editing evaluator: {str(e)}")
                    if not st.session_state.get("popup_dismissed_edit_evaluator_error"):
                        st.session_state["popup_dismissed_edit_evaluator_error"] = True
                        show_error_message("Failed to edit evaluator.", "edit_evaluator_error")
            # Single-click mechanism for Back to Main
            if st.button("Back to Main", key="back_to_main_edit"):
                try:
                    if df_main is None or df_main.empty:
                        raise ValueError("Trainer reports data is missing or empty.")
                    st.session_state.admin_section = "trainer_reports"
                except Exception as e:
                    logger.error(f"Error navigating to trainer reports: {str(e)}")
                    if not st.session_state.get("popup_dismissed_back_to_main_edit_error"):
                        st.session_state["popup_dismissed_back_to_main_edit_error"] = True
                        show_error_message("Failed to navigate to trainer reports.", "back_to_main_edit_error")
        elif section == "delete_evaluator":
            st.markdown("### 🧑‍💻 Delete Evaluator")
            selected_eval = st.selectbox("Select Evaluator to Delete", [""] + evaluators_df["username"].tolist(), key="select_eval_delete")
            if selected_eval:
                if st.button(f"Confirm Delete Evaluator '{selected_eval}'"):
                    try:
                        evaluators_df = evaluators_df[evaluators_df["username"] != selected_eval].reset_index(drop=True)
                        save_evaluators(evaluators_df)
                        st.warning(f"Evaluator '{selected_eval}' deleted.")
                    except Exception as e:
                        logger.error(f"Error deleting evaluator: {str(e)}")
                        if not st.session_state.get("popup_dismissed_delete_evaluator_error"):
                            st.session_state["popup_dismissed_delete_evaluator_error"] = True
                            show_error_message("Failed to delete evaluator.", "delete_evaluator_error")
            # Single-click mechanism for Back to Main
            if st.button("Back to Main", key="back_to_main_delete"):
                try:
                    if df_main is None or df_main.empty:
                        raise ValueError("Trainer reports data is missing or empty.")
                    st.session_state.admin_section = "trainer_reports"
                except Exception as e:
                    logger.error(f"Error navigating to trainer reports: {str(e)}")
                    if not st.session_state.get("popup_dismissed_back_to_main_delete_error"):
                        st.session_state["popup_dismissed_back_to_main_delete_error"] = True
                        show_error_message("Failed to navigate to trainer reports.", "back_to_main_delete_error")
        else:
            try:
                if df_main is None or df_main.empty:
                    raise ValueError("Trainer reports data is missing or empty.")
                st.markdown("---")
                st.markdown("### 📋 Trainer Reports Overview")
                trainer_filter = st.text_input("Filter by Trainer Name or ID", "", help="Press Enter to Apply")
               
                filtered = df_main.copy()
                if trainer_filter:
                    try:
                        mask = filtered["Trainer ID"].astype(str).str.contains(trainer_filter, case=False, na=False) | \
                               filtered["Trainer Name"].astype(str).str.contains(trainer_filter, case=False, na=False)
                        filtered = filtered[mask]
                    except Exception as e:
                        logger.error(f"Error filtering trainers: {str(e)}")
                        if not st.session_state.get("popup_dismissed_trainer_filter_error"):
                            st.session_state["popup_dismissed_trainer_filter_error"] = True
                            show_error_message("Failed to apply trainer filter.", "trainer_filter_error")
                        return
                if not filtered.empty:
                    st.markdown("#### Matching Trainer Assessments")
                    st.dataframe(filtered)
                trainer_ids = sorted(filtered["Trainer ID"].dropna().unique().tolist())
                selected_trainer = st.selectbox("Select Trainer for Detailed Report", [""] + trainer_ids)
                if selected_trainer:
                    trainer_reports = df_main[df_main["Trainer ID"] == selected_trainer]
                    st.markdown(f"##### Reports for Trainer ID: {selected_trainer}")
                    st.dataframe(trainer_reports)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        csv_data = trainer_reports.to_csv(index=False)
                        st.download_button(
                            label="Download Trainer Report CSV",
                            data=csv_data,
                            file_name=f"trainer_{selected_trainer}_reports.csv",
                            mime="text/csv",
                            key=f"download_button_trainer_csv_{selected_trainer}"
                        )
                    with col2:
                        csv_data_all = filtered.to_csv(index=False)
                        st.download_button(
                            label="Download All Filtered Reports CSV",
                            data=csv_data_all,
                            file_name="filtered_trainer_reports.csv",
                            mime="text/csv",
                            key="download_button_filtered_csv"
                        )
                    with col3:
                        try:
                            buffer = BytesIO()
                            pdf = canvas.Canvas(buffer, pagesize=A4)
                            pdf.setFont("Helvetica", 12)
                            y = 750
                            pdf.drawString(100, y, "Evaluator and Trainer Report")
                            y -= 20
                            pdf.drawString(100, y, f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M %p IST')}")
                            y -= 30
                            pdf.drawString(100, y, "Evaluators")
                            y -= 20
                            pdf.setFillColor(colors.black)
                            pdf.drawString(100, y, "Username Full Name Email Role Created At")
                            y -= 20
                            for _, row in evaluators_df.iterrows():
                                text = f"{row['username']} {row['full_name']} {row['email']} {row['role']} {row['created_at']}"
                                pdf.drawString(100, y, text)
                                y -= 20
                                if y < 50:
                                    pdf.showPage()
                                    pdf.setFont("Helvetica", 12)
                                    y = 750
                            y -= 20
                            pdf.drawString(100, y, "Trainers")
                            y -= 20
                            pdf.drawString(100, y, "Trainer ID Trainer Name Branch Department")
                            y -= 20
                            if os.path.exists(DEFAULT_DATA_FILE):
                                trainers_df = pd.read_csv(DEFAULT_DATA_FILE)
                                for _, row in trainers_df.iterrows():
                                    text = f"{row['Trainer ID']} {row['Trainer Name']} {row.get('Branch', '')} {row.get('Department', '')}"
                                    pdf.drawString(100, y, text)
                                    y -= 20
                                    if y < 50:
                                        pdf.showPage()
                                        pdf.setFont("Helvetica", 12)
                                        y = 750
                            pdf.showPage()
                            pdf.save()
                            pdf_data = buffer.getvalue()
                            buffer.close()
                            st.download_button(
                                label="Download Evaluators/Trainers PDF",
                                data=pdf_data,
                                file_name="evaluators_trainers_report.pdf",
                                mime="application/pdf",
                                key="download_button_admin_pdf"
                            )
                        except Exception as e:
                            logger.error(f"Error generating PDF: {str(e)}")
                            if not st.session_state.get("popup_dismissed_pdf_report_error"):
                                st.session_state["popup_dismissed_pdf_report_error"] = True
                                st.markdown("""
                                <div class="error-popup show-popup" id="popup_pdf_report_error">
                                    <p>Failed to generate PDF report.</p>
                                    <button class="ok-button" onclick="document.getElementById('popup_{key}').remove()">OK</button>
                                </div>
                                <script>
                                    function closePopup(key) {{
                                        var popup = document.getElementById('popup_' + key);
                                        popup.remove();  // Directly removes the popup from the DOM
                                        
                                    }}
                                </script>
                                """, unsafe_allow_html=True)
            except Exception as e:
                logger.error(f"Error in trainer reports section: {str(e)}")
                if not st.session_state.get("popup_dismissed_trainer_reports_error"):
                    st.session_state["popup_dismissed_trainer_reports_error"] = True
                    st.markdown("""
                    <div class="error-popup show-popup" id="popup_trainer_reports_error">
                        <p>Failed to load trainer reports.</p>
                        <button class="ok-button" onclick="document.getElementById('popup_{key}').remove()">OK</button>
                    </div>
                    <script>
                        function closePopup(key) {{
                            var popup = document.getElementById('popup_' + key);
                            popup.remove();  // Directly removes the popup from the DOM
                            
                        }}
                    </script>
                    """, unsafe_allow_html=True)
        # NEW Button: DOWNLOAD EVALUATORS
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M")
        evaluators_csv_data = evaluators_df.to_csv(index=False)
        st.download_button(
            label="DOWNLOAD EVALUATORS",
            data=evaluators_csv_data,
            file_name=f"evaluators_{timestamp}.csv",
            mime="text/csv",
            key="download_evaluators_csv"
        )
        if st.button("Logout", key="admin_logout"):
            try:
                for key in ["logged_in", "role", "logged_user"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Logged out successfully!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
                if not st.session_state.get("popup_dismissed_admin_logout_error"):
                    st.session_state["popup_dismissed_admin_logout_error"] = True
                    st.markdown("""
                    <div class="error-popup show-popup" id="popup_admin_logout_error">
                        <p>Failed to logout. Please try again.</p>
                        <button class="ok-button" onclick="document.getElementById('popup_{key}').remove()">OK</button>
                    </div>
                    <script>
                        function closePopup(key) {{
                            var popup = document.getElementById('popup_' + key);
                            popup.remove();  // Directly removes the popup from the DOM
                            
                        }}
                    </script>
                    """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error in admin section: {str(e)}")
        if not st.session_state.get("popup_dismissed_admin_dashboard_error"):
            st.session_state["popup_dismissed_admin_dashboard_error"] = True
            st.markdown("""
            <div class="error-popup show-popup" id="popup_admin_dashboard_error">
                <p>An unexpected error occurred in the Admin Dashboard.</p>
                <button class="ok-button" onclick="document.getElementById('popup_{key}').remove()">OK</button>
            </div>
            <script>
                function closePopup(key) {{
                    var popup = document.getElementById('popup_' + key);
                    popup.remove();  // Directly removes the popup from the DOM
                    
                }}
            </script>
            """, unsafe_allow_html=True)
                    
def set_background(image_file):
    try:
        with open(image_file, "rb") as image:
            img_bytes = base64.b64encode(image.read()).decode()
        page_bg_img = f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{img_bytes}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error setting background: {str(e)}")
        st.error("Failed to set background image.")

def login_ui():
    try:
        st.sidebar.title("🔐 Login Panel")

        role = st.radio("Select Role", ["Viewer", "Evaluator", "Super_Administrator"])
        #bg_image = f"background{'' if role == 'Viewer' else '1' if role == 'Evaluator' else '2'}.jpg"
        bg_image = f"backgroundimage{'5' if role == 'Viewer' else '3' if role == 'Evaluator' else '6'}.png"
        if os.path.exists(bg_image):
            set_background(bg_image)

        col1, col2 = st.columns([4, 1])

        with col1:
            st.title("🧑‍💼 Assessment Login Form")
            username = st.text_input("Username", key="username_input")
            password = st.text_input("Password", type="password", key="password_input")
            login_btn = st.button("🔓 Login")

            if login_btn:
                try:
                    if (role == "Viewer" and username == "omotec" and password == "omotec") or \
                       (role == "Evaluator" and username == "omotec1" and password == "omotec123") or \
                       (role == "Super_Administrator" and username == "omotec2" and password == "omotec@123#"):
                        st.session_state.logged_in = True
                        st.session_state["role"] = role.replace("_", " ")
                        st.session_state["logged_user"] = username
                        st.success(f"✅ Logged in successfully as {role.replace('_', ' ')}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid Login Credentials")
                except Exception as e:
                    logger.error(f"Error during login: {str(e)}")
                    st.error("Failed to process login. Please try again.")

        with col2:
            if os.path.exists("NEW LOGO - OMOTEC.png"):
                st.image("NEW LOGO - OMOTEC.png", use_column_width=True)
    except Exception as e:
        logger.error(f"Error in login UI: {str(e)}")
        st.error("An unexpected error occurred in the Login Panel.")

def main():
    try:
        if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
            login_ui()
        else:
            df_main = load_data()
            role = st.session_state.get("role", "")
            if role == "Evaluator":
                evaluator_section(df_main)
            elif role == "Viewer":
                viewer_section(df_main)
            elif role == "Super Administrator":
                admin_section(df_main)
            else:
                st.warning("Invalid role. Please login with a valid role.")
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        st.error("An unexpected error occurred in the application.")

if __name__ == "__main__":
    main()