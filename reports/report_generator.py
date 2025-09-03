from fpdf import FPDF

def generate_report(business_name, analysis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"{business_name} - Online Presence Report", ln=True)
    for k, v in analysis.items():
        pdf.cell(200, 10, txt=f"{k}: {v}", ln=True)
    filepath = f"./data/{business_name.replace(' ', '_')}_report.pdf"
    pdf.output(filepath)
    return filepath
