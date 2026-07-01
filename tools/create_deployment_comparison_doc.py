from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Deployment_Options_Comparison.docx"


def set_run_font(run, size=10.5, bold=False, color="10233F"):
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def add_heading(doc, text, level=1):
    paragraph = doc.add_paragraph()
    paragraph.style = f"Heading {level}"
    run = paragraph.add_run(text)
    run.font.name = "Arial"
    run.bold = True
    run.font.color.rgb = RGBColor.from_string("0B57D0" if level <= 2 else "10233F")
    if level == 1:
        run.font.size = Pt(16)
    elif level == 2:
        run.font.size = Pt(13)
    else:
        run.font.size = Pt(11.5)
    return paragraph


def add_para(doc, text="", bold_prefix=None):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(6)
    if bold_prefix and text.startswith(bold_prefix):
        run = paragraph.add_run(bold_prefix)
        set_run_font(run, bold=True)
        run = paragraph.add_run(text[len(bold_prefix):])
        set_run_font(run)
    else:
        run = paragraph.add_run(text)
        set_run_font(run)
    return paragraph


def add_bullets(doc, items):
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(2)
        set_run_font(paragraph.add_run(item))


def add_numbered(doc, items):
    for item in items:
        paragraph = doc.add_paragraph(style="List Number")
        paragraph.paragraph_format.space_after = Pt(2)
        set_run_font(paragraph.add_run(item))


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        paragraph = hdr_cells[i].paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(header)
        set_run_font(run, size=9.5, bold=True, color="FFFFFF")
        shading = hdr_cells[i]._tc.get_or_add_tcPr()
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "0B57D0")
        shading.append(shd)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cells[i].paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run(value)
            set_run_font(run, size=9.5)
    doc.add_paragraph()
    return table


def build_doc():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Deployment Options Comparison")
    set_run_font(run, size=20, bold=True, color="0B57D0")
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Submittal Preparation System")
    set_run_font(run, size=13, bold=True)
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta.add_run("Prepared for Management Review | Date: 01 July 2026")
    set_run_font(run, size=9.5, color="667893")

    add_heading(doc, "1. Purpose", 1)
    add_para(doc, "This document compares the available deployment options for the Submittal Preparation System. The system is currently running locally and includes the frontend web application, FastAPI backend, PostgreSQL database, user/admin role management, product/document management, template management, and automated final PDF generation.")

    add_heading(doc, "2. Important Current Server Note", 1)
    add_para(doc, "Based on the current information, the company server available now appears to be mainly a file storage server. A file storage server is normally used for shared folders and company document storage.")
    add_para(doc, "It may not be suitable for directly hosting this web application unless IT provides a separate deployable application server or virtual machine.")
    add_para(doc, "For internal deployment, IT should ideally provide:")
    add_bullets(doc, [
        "Linux server or Linux virtual machine",
        "Docker and Docker Compose support",
        "Sufficient CPU, RAM, and storage",
        "Database backup facility",
        "Internal network access for employees",
        "Optional VPN or controlled external access if required",
    ])

    add_heading(doc, "3. Options Compared", 1)
    add_table(doc, ["Option", "Estimated Cost", "Ease", "Control", "Best Use"], [
        ["Company Linux Server / VM", "Lowest if provided internally", "Medium", "High", "Internal company use"],
        ["AWS EC2 Cloud Server", "USD 25–50/month approx.", "Medium", "Very High", "Long-term production/cloud access"],
        ["Railway Cloud Platform", "USD 5–25/month approx.", "Easy", "Medium", "Quick trial/demo deployment"],
    ])

    add_heading(doc, "4. Company Linux Server / Virtual Machine", 1)
    add_para(doc, "This option means IT provides a deployable Linux server or Linux VM within the company network. The system would run using Docker Compose on that server.")
    add_heading(doc, "Advantages", 2)
    add_bullets(doc, [
        "Lowest recurring cost if company infrastructure is available.",
        "Company data remains inside the company network.",
        "Good for internal users.",
        "Better control over access, documents, and backups.",
        "No dependency on monthly cloud billing.",
    ])
    add_heading(doc, "Disadvantages", 2)
    add_bullets(doc, [
        "The current file storage server may not be suitable for application deployment.",
        "Requires IT support for setup, maintenance, backups, and security.",
        "External access requires VPN, firewall, or secure remote access configuration.",
        "Availability depends on company server and network uptime.",
    ])
    add_para(doc, "Best suited for: Internal company use where employees access the system from office network or VPN.", "Best suited for:")

    add_heading(doc, "5. AWS EC2 Cloud Server", 1)
    add_para(doc, "This option means deploying the application on an AWS Linux server. The frontend, backend, and PostgreSQL database can run using Docker Compose on one EC2 instance.")
    add_table(doc, ["Item", "Approx. Cost"], [
        ["EC2 Linux server", "USD 15–35/month"],
        ["EBS storage", "USD 3–8/month"],
        ["Public IPv4 address", "Approx. USD 3.60/month"],
        ["Data transfer", "Usually low; AWS includes 100 GB/month free data transfer out"],
        ["SSL certificate", "Free using Let’s Encrypt"],
        ["Domain", "Optional, usually USD 10–15/year"],
    ])
    add_para(doc, "Estimated total: USD 25–50/month approximately. If AWS RDS PostgreSQL is used separately, the cost can increase significantly. For the first production version, a PostgreSQL container on the EC2 server is a lower-cost approach.")
    add_heading(doc, "Advantages", 2)
    add_bullets(doc, [
        "Good option for long-term production use.",
        "Accessible from outside the office using a secure domain.",
        "Suitable for remote users and multiple branches.",
        "More scalable than an internal file server.",
        "Full control over server configuration.",
        "Backups and monitoring can be configured professionally.",
    ])
    add_heading(doc, "Disadvantages", 2)
    add_bullets(doc, [
        "Monthly cloud cost.",
        "Requires cloud/server administration.",
        "Security, firewall, SSL, and backups must be configured carefully.",
        "Costs can increase if extra AWS services are added.",
    ])

    add_heading(doc, "6. Railway Cloud Platform", 1)
    add_para(doc, "Railway is a cloud deployment platform that is easier to set up than AWS. The application would usually be deployed as separate frontend, backend API, and PostgreSQL database services.")
    add_table(doc, ["Usage Type", "Approx. Cost"], [
        ["Small test deployment", "USD 5–10/month"],
        ["Normal light company usage", "USD 10–25/month"],
        ["Heavier usage/document storage", "USD 25+/month"],
    ])
    add_heading(doc, "Advantages", 2)
    add_bullets(doc, [
        "Fastest and easiest cloud deployment option.",
        "Good for demo or trial usage.",
        "Built-in database options.",
        "Public URL available quickly.",
        "Less server maintenance compared to AWS.",
    ])
    add_heading(doc, "Disadvantages", 2)
    add_bullets(doc, [
        "Less control compared to AWS or a company server.",
        "Current Docker Compose setup may need adjustment.",
        "Costs can increase with storage, traffic, and usage.",
        "Not the preferred final option if the company requires full infrastructure control.",
    ])

    add_heading(doc, "7. Recommendation", 1)
    add_para(doc, "First preference: Request IT to provide a low-cost deployable Linux server or Linux virtual machine. This is the best option if the system is mainly for internal company use because it keeps company documents and data within the company network and avoids recurring cloud hosting costs.")
    add_para(doc, "Second preference: Use AWS EC2 if IT cannot provide a suitable deployable server, if users need access from outside the office, or if the system is approved for long-term production use.")
    add_para(doc, "Temporary trial option: Use Railway if a quick online demo or selected-user test is needed before final production hosting is selected.")

    add_heading(doc, "8. Required Confirmation from IT", 1)
    add_numbered(doc, [
        "Can a Linux server or Linux VM be provided for application deployment?",
        "Can Docker and Docker Compose be installed?",
        "What CPU, RAM, and storage can be allocated?",
        "Will users access the system internally only or remotely as well?",
        "Can a company domain or internal URL be assigned?",
        "How will database and uploaded PDF backups be handled?",
        "Who will maintain server updates, SSL, firewall, and security?",
    ])

    add_heading(doc, "9. Final Summary", 1)
    add_para(doc, "For internal company use, the recommended option is a company-provided Linux server or VM. For external/remote access and long-term cloud production, AWS EC2 is the recommended option. For a quick temporary online trial, Railway is the easiest option.")
    add_para(doc, "The existing file storage server should not be assumed suitable for deployment unless IT confirms that it can safely run application services, Docker containers, and PostgreSQL.")

    add_heading(doc, "10. Reference Links", 1)
    add_bullets(doc, [
        "AWS EC2 pricing: https://aws.amazon.com/ec2/pricing/on-demand/",
        "AWS EBS pricing: https://aws.amazon.com/ebs/pricing/",
        "AWS VPC public IPv4 pricing: https://aws.amazon.com/vpc/pricing/",
        "Railway pricing: https://railway.com/pricing",
    ])

    OUT.parent.mkdir(exist_ok=True)
    doc.save(OUT)


if __name__ == "__main__":
    build_doc()
    print(OUT)
