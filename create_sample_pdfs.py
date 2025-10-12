from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from pathlib import Path

def create_sample_pdfs():
    """Cria PDFs de exemplo para teste"""
    
    output_dir = Path("./documentos")
    output_dir.mkdir(exist_ok=True)
    
    # PDF 1: Relatório de Absenteísmo
    create_absenteismo_pdf(output_dir / "relatorio_absenteismo_2024.pdf")
    
    # PDF 2: Tabela de Custos
    create_custos_pdf(output_dir / "tabela_custos_sus.pdf")
    
    # PDF 3: Políticas e Protocolos
    create_politicas_pdf(output_dir / "protocolos_atendimento.pdf")
    
    print("✅ PDFs de exemplo criados em ./documentos/")

def create_absenteismo_pdf(filename):
    doc = SimpleDocTemplate(str(filename), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title = Paragraph("RELATÓRIO DE ABSENTEÍSMO - 2024<br/>Secretaria de Saúde do RJ", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Texto
    text = """
    <b>DADOS GERAIS</b><br/>
    Período de análise: Janeiro a Setembro de 2024<br/>
    Total de consultas agendadas: 125.430<br/>
    Total de comparecimentos: 93.872 (74.8%)<br/>
    Total de faltas (no-show): 31.558 (25.2%)<br/><br/>
    
    <b>DISTRIBUIÇÃO POR ESPECIALIDADE</b><br/>
    As especialidades com maior taxa de absenteísmo foram:<br/>
    - Cardiologia: 32.4% de no-show<br/>
    - Ortopedia: 28.7% de no-show<br/>
    - Dermatologia: 23.1% de no-show<br/>
    - Oftalmologia: 22.3% de no-show<br/>
    - Pediatria: 18.2% de no-show<br/><br/>
    
    <b>PADRÕES TEMPORAIS</b><br/>
    Dias com maior absenteísmo:<br/>
    - Segunda-feira: 31.2%<br/>
    - Sexta-feira: 29.8%<br/>
    - Quarta-feira: 24.5%<br/>
    - Terça e Quinta: 22.1%<br/><br/>
    
    <b>PERFIL DEMOGRÁFICO</b><br/>
    Faixa etária com maior no-show:<br/>
    - 19-30 anos: 34.2%<br/>
    - 31-45 anos: 26.8%<br/>
    - 46-60 anos: 22.1%<br/>
    - 61+ anos: 15.3%<br/>
    - 0-18 anos: 19.7%<br/>
    """
    
    story.append(Paragraph(text, styles['Normal']))
    
    doc.build(story)

def create_custos_pdf(filename):
    doc = SimpleDocTemplate(str(filename), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("TABELA DE CUSTOS - SUS<br/>Valores de Referência 2024", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Tabela de custos
    data = [
        ['Especialidade', 'Custo Consulta', 'Custo Hora Médico', 'Custo Estrutura'],
        ['Cardiologia', 'R$ 156,00', 'R$ 180,00/h', 'R$ 45,00'],
        ['Ortopedia', 'R$ 142,00', 'R$ 165,00/h', 'R$ 38,00'],
        ['Pediatria', 'R$ 89,00', 'R$ 95,00/h', 'R$ 28,00'],
        ['Dermatologia', 'R$ 98,00', 'R$ 110,00/h', 'R$ 32,00'],
        ['Oftalmologia', 'R$ 112,00', 'R$ 125,00/h', 'R$ 35,00'],
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    text = """
    <b>CUSTOS DE INTERVENÇÕES</b><br/><br/>
    SMS: R$ 0,12 por mensagem<br/>
    Ligação telefônica: R$ 2,50 por ligação (custo médio 3 min)<br/>
    Email: R$ 0,05 por envio<br/><br/>
    
    <b>CUSTOS INDIRETOS</b><br/>
    Custo de vaga ociosa: Custo da consulta + 60% (estrutura, equipe, materiais)<br/>
    Custo de overbooking (se houver sobrecarga): R$ 85,00 por paciente extra (tempo adicional, estresse da equipe)<br/>
    """
    
    story.append(Paragraph(text, styles['Normal']))
    
    doc.build(story)

def create_politicas_pdf(filename):
    doc = SimpleDocTemplate(str(filename), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    title = Paragraph("PROTOCOLOS DE ATENDIMENTO<br/>Política de Overbooking e Intervenções", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    text = """
    <b>1. POLÍTICA DE OVERBOOKING</b><br/><br/>
    
    A Secretaria de Saúde autoriza overbooking inteligente seguindo os seguintes critérios:<br/><br/>
    
    1.1 Percentuais Máximos Autorizados:<br/>
    - Especialidades com histórico de no-show >25%: até 15% de overbooking<br/>
    - Especialidades com no-show 15-25%: até 10% de overbooking<br/>
    - Especialidades com no-show <15%: até 5% de overbooking<br/><br/>
    
    1.2 Monitoramento Obrigatório:<br/>
    - Avaliação diária de sobrecarga<br/>
    - Limite de sobrecarga real: máximo 5% acima da capacidade<br/>
    - Suspensão automática se sobrecarga >5% por 3 dias consecutivos<br/><br/>
    
    <b>2. PROTOCOLO DE INTERVENÇÕES PREVENTIVAS</b><br/><br/>
    
    2.1 Segmentação de Pacientes:<br/>
    - Risco ALTO (>60% probabilidade no-show): Ligação telefônica 48h antes + SMS 24h antes<br/>
    - Risco MÉDIO (30-60%): SMS 24h antes<br/>
    - Risco BAIXO (<30%): Confirmação automática no agendamento<br/><br/>
    
    2.2 Scripts Aprovados:<br/>
    Ligação: "Olá [nome], aqui é [atendente] da Secretaria de Saúde. Estamos confirmando sua consulta de [especialidade] dia [data] às [hora]. Você consegue comparecer? Caso tenha alguma dificuldade, podemos ajudar com remarcação ou transporte."<br/><br/>
    
    SMS: "Lembrete: Consulta de [especialidade] amanhã às [hora] na [unidade]. Em caso de imprevistos, ligue [telefone] para remarcar. Sua presença é importante!"<br/><br/>
    
    <b>3. PROGRAMA DE EQUIDADE</b><br/><br/>
    
    3.1 Populações Prioritárias:<br/>
    - Idosos (60+): Preferência por ligação, horários flexíveis<br/>
    - Baixa renda (até 2 salários mínimos): Auxílio transporte disponível<br/>
    - Áreas remotas (>10km da unidade): Prioridade em agendas, transporte facilitado<br/><br/>
    
    3.2 Auxílio Transporte:<br/>
    - Critério: Renda <2 SM + Distância >10km + Consulta prioritária<br/>
    - Valor: Até R$ 20,00 por consulta (ida e volta)<br/>
    - Orçamento mensal: R$ 15.000,00<br/>
    """
    
    story.append(Paragraph(text, styles['Normal']))
    
    doc.build(story)

if __name__ == "__main__":
    create_sample_pdfs()