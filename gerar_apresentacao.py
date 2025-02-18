from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from datetime import datetime

def generate_presentation():
    # Create the PDF document
    doc = SimpleDocTemplate(
        "WEG_VDI_Automation_Presentation.pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.HexColor('#00529b')  # WEG Blue
    )

    # Title
    elements.append(Paragraph("Automação de Solicitação VDI", title_style))
    elements.append(Paragraph("WEG TIN - Tecnologia de Infraestrutura", subtitle_style))
    elements.append(Spacer(1, 30))

    # Overview
    elements.append(Paragraph("Visão Geral", subtitle_style))
    overview_text = """
    O aplicativo de Solicitação VDI (Desktop Virtual) automatiza o processo de requisição 
    de máquinas virtuais na plataforma AWX, proporcionando uma interface intuitiva e eficiente 
    para os usuários da WEG.
    """
    elements.append(Paragraph(overview_text, styles['Normal']))
    elements.append(Spacer(1, 20))

    # Key Features
    elements.append(Paragraph("Funcionalidades Principais", subtitle_style))
    features = [
        ["• Integração com Office 365", "Busca automática de usuários"],
        ["• Validação Automática", "Verificação de duplicidade de VMs"],
        ["• Workflow de Aprovação", "Processo automatizado de autorização do gestor"],
        ["• Interface Intuitiva", "Formulário simplificado no Power Apps"],
        ["• Integração SharePoint", "Armazenamento centralizado de dados"]
    ]
    
    t = Table(features, colWidths=[200, 250])
    t.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#00529b')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Technical Details
    elements.append(Paragraph("Detalhes Técnicos", subtitle_style))
    tech_text = """
    • Desenvolvido em Power Apps com integração Office 365
    • Automatização via AWX para provisionamento de VMs
    • Base de dados em SharePoint para gestão de solicitações
    • Sistema de notificações automáticas
    • Validações em tempo real dos dados inseridos
    """
    elements.append(Paragraph(tech_text, styles['Normal']))
    elements.append(Spacer(1, 20))

    # Benefits
    elements.append(Paragraph("Benefícios", subtitle_style))
    benefits_text = """
    • Redução do tempo de provisioning de VMs
    • Eliminação de erros manuais no processo
    • Maior controle e rastreabilidade das solicitações
    • Interface padronizada e amigável
    • Processo de aprovação transparente
    """
    elements.append(Paragraph(benefits_text, styles['Normal']))

    # Generate the PDF
    doc.build(elements)

if __name__ == '__main__':
    generate_presentation()
