import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io

st.set_page_config(page_title="Mesclagem de PDFs Compilado", layout="wide")
st.title("📘 Mesclagem de PDFs para Compilado de Documentos")

# ===============================
# INTERFACE DO USUÁRIO
# ===============================
st.subheader("📌 PDF Mãe")
pdf_mae_file = st.file_uploader("Selecione o Compilado", type=["pdf"])

st.markdown("---")

# Títulos personalizados para os anexos (ATUALIZADOS)
titulos_anexos = [
    "Anexo I - Layout da área de armazenamento das bobinas OCYME com requisitos de SMS representados",
    "Anexo II - Layout Base TFMC – Localizações, extintores, pontos de encontro etc.",
    "Anexo III - Inspeção de Tubos Flexíveis Umbilicais e Acessórios Montados",
    "Anexo IV - Matriz de Treinamento Normativo",
    "Anexo V - Transporte de Bobinas com JUMBO",
    "Anexo VI - Plano de Manutenção para Máquinas e Equipamentos",
    "Anexo VII - Plano de Atendimento a Emergência",
    "Anexo VIII - Procedimento de Manutenção em Máquinas e Equipamentos",
    "Anexo IX - Içamento e Movimentação de Cargas",
    "Anexo X - Identificação armazenamento, inspeção e teste",
    "Anexo XI - Permissão de Trabalho",
    "Anexo XII - Comunicação Análise e Abrangência de Ocorrências",
    "Anexo XIII - Identificação de Perigo e Avaliação de Risco",
    "Anexo XIV - Sistemática da segurança de equipamentos críticos",
    "Anexo XV - Plano de içamento de bobinas do consórcio",
    "Anexo XVI - Plano de posicionamento de bobinas nos slots de armazenamento"
]

# Uploads por anexo (cria 16 seções de upload)
capitulos = {}
for i, titulo in enumerate(titulos_anexos, start=1):
    st.markdown(f"### 📎 {titulo}")
    files = st.file_uploader(
        f"Envie os arquivos para {titulo}",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"cap_{i}"
    )
    capitulos[f"cap_{i}"] = files

st.markdown("---")

# Coordenadas da numeração
st.subheader("✍️ Posição da Numeração (X e Y)")
colx, coly = st.columns(2)
with colx:
    pos_x = st.number_input("Coordenada X", min_value=0, max_value=1000, value=503)
with coly:
    pos_y = st.number_input("Coordenada Y", min_value=0, max_value=1000, value=735)

# Nome do arquivo final
nome_arquivo = st.text_input("📝 Nome do arquivo final (sem .pdf)", value="Relatorio_Final")

# ===============================
# FUNÇÕES DE PROCESSAMENTO
# ===============================
def processar_pdfs(pdf_mae_file, capitulos, pos_x, pos_y, titulos_anexos):
    reader = PdfReader(pdf_mae_file)
    total_paginas = len(reader.pages)

    # Número de capítulos é definido pela quantidade de títulos configurados
    num_capitulos = len(titulos_anexos)

    if total_paginas < num_capitulos:
        raise Exception(
            f"O PDF Mãe precisa ter pelo menos {num_capitulos} páginas de capa "
            f"(uma para cada anexo). Ele atualmente tem {total_paginas} página(s)."
        )

    # Divide PDF Mãe: corpo e as 'capas' (últimas N páginas)
    corpo_principal = reader.pages[:-num_capitulos]
    capas = reader.pages[-num_capitulos:]

    paginas_finais = []
    indices_mae_para_enum = []

    # Adiciona corpo do PDF mãe com numeração
    for _i, pagina in enumerate(corpo_principal):
        paginas_finais.append(pagina)
        indices_mae_para_enum.append(len(paginas_finais) - 1)

    # Para cada anexo: adiciona a capa correspondente + anexos enviados (se houver)
    for idx in range(num_capitulos):
        capa = capas[idx]
        paginas_finais.append(capa)
        indices_mae_para_enum.append(len(paginas_finais) - 1)

        # Anexos deste capítulo
        arquivos_anexos = capitulos.get(f"cap_{idx+1}", [])
        for file in arquivos_anexos or []:
            leitor_anexo = PdfReader(file)
            for pagina_anexo in leitor_anexo.pages:
                paginas_finais.append(pagina_anexo)
                # Anexos não entram na enumeração

    # Cria PDF temporário com todas as páginas mescladas
    writer_temp = PdfWriter()
    for pagina in paginas_finais:
        writer_temp.add_page(pagina)

    temp_bytes = io.BytesIO()
    writer_temp.write(temp_bytes)
    temp_bytes.seek(0)

    return adicionar_numeracao(temp_bytes, indices_mae_para_enum, pos_x, pos_y)

def adicionar_numeracao(pdf_stream, indices_para_numerar, pos_x, pos_y):
    reader = PdfReader(pdf_stream)
    writer = PdfWriter()
    total_paginas = len(reader.pages)

    for i, pagina in enumerate(reader.pages):
        if i in indices_para_numerar:
            largura = float(pagina.mediabox.width)
            altura = float(pagina.mediabox.height)

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(largura, altura))
            texto = f"{i + 1}/{total_paginas}"
            can.setFont("Helvetica-Bold", 10)
            can.drawString(pos_x, pos_y, texto)
            can.save()
            packet.seek(0)

            overlay = PdfReader(packet)
            pagina.merge_page(overlay.pages[0])

        writer.add_page(pagina)

    final_bytes = io.BytesIO()
    writer.write(final_bytes)
    final_bytes.seek(0)
    return final_bytes

# Botão de geração
if st.button("🚀 Gerar Relatório Final"):
    if not pdf_mae_file:
        st.error("⚠️ PDF Mãe é obrigatório.")
    else:
        try:
            output_pdf = processar_pdfs(pdf_mae_file, capitulos, pos_x, pos_y, titulos_anexos)
            st.success("✅ PDF Gerado com Sucesso!")
            st.download_button(
                label="📥 Baixar PDF Final",
                data=output_pdf,
                file_name=f"{nome_arquivo.strip()}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"❌ Erro ao processar: {e}")

# ===============================
# RODAPÉ DE AUTORIA
# ===============================
st.markdown(
    """
<style>
   .rodape {
       position: fixed;
       bottom: 10px;
       left: 0;
       width: 100%;
       text-align: center;
       font-size: 13px;
       color: #888888;
       z-index: 100;
   }
</style>
<div class="rodape">
   Criado por: <strong>Diugo Silvano</strong>
</div>
    """,
    unsafe_allow_html=True
)
