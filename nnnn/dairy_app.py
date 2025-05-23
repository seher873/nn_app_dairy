import streamlit as st
import sqlite3
from fpdf import FPDF
from datetime import datetime
import os

# ---------------------------
# Database Operations Class
# ---------------------------
class DairyDB:
    def __init__(self, db_name="dairy.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                date TEXT,
                shift TEXT,
                mound REAL,
                kg REAL,
                rate REAL
            )
        """)
        self.conn.commit()

    def add_record(self, name, date, shift, mound, kg, rate):
        self.conn.execute("INSERT INTO records (name, date, shift, mound, kg, rate) VALUES (?, ?, ?, ?, ?, ?)",
                          (name, date, shift, mound, kg, rate))
        self.conn.commit()

    def get_records(self, name, date):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM records WHERE name = ? AND date = ?", (name, date))
        return cur.fetchall()

    def get_all_records(self, name):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM records WHERE name = ? ORDER BY date", (name,))
        return cur.fetchall()

    def delete_record(self, record_id):
        self.conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        self.conn.commit()

# ---------------------------
# PDF Export Function
# ---------------------------
def export_pdf(name, records):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(0, 51, 102)  # Dark blue color

        # Title & Name at top
        pdf.cell(0, 10, "Malik Obaid Dairy Record", ln=True, align="C")
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Customer Name: {name}", ln=True, align="C")
        pdf.ln(10)

        headers = ["Date", "Shift", "Mound", "Kg", "Rate", "Total"]
        col_widths = [30, 30, 25, 25, 25, 25]

        # Header row with background color
        pdf.set_fill_color(200, 220, 255)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, fill=True, align='C')
        pdf.ln()

        total_mound = 0
        total_kg = 0

        for rec in records:
            _, _, rec_date, shift, mound, kg, rate = rec
            total = mound * rate if rate else 0
            total_mound += mound
            total_kg += kg

            pdf.cell(col_widths[0], 10, str(rec_date), border=1)
            pdf.cell(col_widths[1], 10, str(shift), border=1)
            pdf.cell(col_widths[2], 10, f"{mound:.2f}", border=1, align='R')
            pdf.cell(col_widths[3], 10, f"{kg:.2f}", border=1, align='R')
            pdf.cell(col_widths[4], 10, f"{rate:.2f}" if rate else "N/A", border=1, align='R')
            pdf.cell(col_widths[5], 10, f"{total:.2f}" if rate else "N/A", border=1, align='R')
            pdf.ln()

        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Total Mound: {total_mound:.2f}", ln=True)
        pdf.cell(0, 10, f"Total Kg: {total_kg:.2f}", ln=True)

        # Save PDF to a local folder "exports"
        output_folder = "exports"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        file_name = f"{name}_dairy.pdf".replace(" ", "_")
        file_path = os.path.join(output_folder, file_name)
        pdf.output(file_path)
        return file_path
    except Exception as e:
        st.error(f"PDF export failed: {e}")
        return None

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🐼 Dairy Entry App")

db = DairyDB()

name = st.text_input("Customer Name")
date = st.date_input("Date", value=datetime.today()).strftime("%Y-%m-%d")
shift = st.selectbox("Shift", ["Morning", "Evening"])
mound = st.number_input("Mound", min_value=0.0, format="%.2f")
kg = st.number_input("Kg", min_value=0.0, format="%.2f")
rate = st.number_input("Rate (optional)", min_value=0.0, format="%.2f", value=0.0)

if st.button("Add Entry"):
    if not name.strip():
        st.error("Please enter a customer name.")
    else:
        try:
            db.add_record(name, date, shift, mound, kg, rate)
            st.success("Record added successfully.")
        except Exception as e:
            st.error(f"Failed to add record: {e}")

records = db.get_all_records(name) if name else []

if records:
    st.subheader(f"Saved Records for {name}")

    current_date = None

    for rec in records:
        rec_id, _, rec_date, shift, mound_val, kg_val, rate_val = rec

        # Print date header if changed
        if rec_date != current_date:
            st.markdown(f"### Date: {rec_date}")
            current_date = rec_date

        rate_str = f"{rate_val:.2f}" if rate_val else "N/A"
        st.write(f"**Shift:** {shift}, Mound: {mound_val:.2f}, Kg: {kg_val:.2f}, Rate: {rate_str}")

        if st.button(f"Delete Entry {rec_id}", key=f"delete_{rec_id}"):
            try:
                db.delete_record(rec_id)
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to delete record: {e}")

    if st.button("📄 Export PDF"):
        path = export_pdf(name, records)
        if path:
            with open(path, "rb") as file:
                st.download_button(label="Download PDF", data=file, file_name=os.path.basename(path))

else:
    if name:
        st.info("No records found for this customer.")
    else:
        st.info("Please enter a customer name to see records.")
