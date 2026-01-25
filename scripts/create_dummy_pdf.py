from fpdf import FPDF
import os

def create_dummy_cv(output_path):
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "John Doe", ln=True)
    
    # Contact Info
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, "Software Engineer | janedoe@example.com", ln=True)
    pdf.cell(0, 10, "San Francisco, CA | (555) 123-4567", ln=True)
    
    pdf.ln(10)
    
    # Experience
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Experience", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Senior Developer | Tech Solutions", ln=True)
    pdf.set_font("Arial", "I", 12)
    pdf.cell(0, 10, "June 2020 - Present", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, "- Lead developer for the main product.\n- Managed a team of 5 engineers.\n- Optimized database queries reducing load times by 50%.")
    
    pdf.ln(5)
    
    # Education
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Education", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "University of Technology", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, "B.S. in Computer Science", ln=True)
    
    # Save
    pdf.output(output_path)
    print(f"Created: {output_path}")

if __name__ == "__main__":
    os.makedirs("data/raw", exist_ok=True)
    create_dummy_cv("data/raw/dummy_cv.pdf")
