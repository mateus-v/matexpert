import streamlit as st
import io
import zipfile
from PIL import Image
import base64
from typing import List, Tuple

# Configuração da página
st.set_page_config(
    page_title="Conversor PNG → WEBP | PMCs SoftExpert",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .stats-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def convert_image_to_webp(image_data: bytes, filename: str, quality: int, lossless: bool) -> Tuple[bytes, dict]:
    """
    Converte uma imagem para WEBP
    
    Args:
        image_data: Dados da imagem em bytes
        filename: Nome do arquivo original
        quality: Qualidade da compressão (0-100)
        lossless: Se usar compressão sem perdas
    
    Returns:
        Tuple com os dados da imagem convertida e estatísticas
    """
    try:
        # Abrir imagem
        image = Image.open(io.BytesIO(image_data))
        
        # Converter RGBA para RGB se necessário
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        elif image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        
        # Converter para WEBP
        output_buffer = io.BytesIO()
        
        if lossless:
            image.save(output_buffer, 'WEBP', lossless=True)
            compression_type = "Sem perdas"
        else:
            image.save(output_buffer, 'WEBP', quality=quality, optimize=True)
            compression_type = f"Qualidade {quality}"
        
        webp_data = output_buffer.getvalue()
        
        # Calcular estatísticas
        original_size = len(image_data)
        new_size = len(webp_data)
        reduction = (1 - new_size / original_size) * 100
        
        stats = {
            'filename': filename,
            'original_size': original_size,
            'new_size': new_size,
            'reduction': reduction,
            'compression_type': compression_type,
            'dimensions': f"{image.size[0]}x{image.size[1]}"
        }
        
        return webp_data, stats
        
    except Exception as e:
        st.error(f"Erro ao converter {filename}: {str(e)}")
        return None, None

def create_download_link(data: bytes, filename: str, text: str) -> str:
    """Cria um link de download para os dados"""
    b64_data = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64_data}" download="{filename}">{text}</a>'
    return href

def format_bytes(bytes_value: int) -> str:
    """Formata bytes em unidades legíveis"""
    for unit in ['B', 'KB', 'MB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} GB"

def main():
    # Título principal
    st.markdown('<h1 class="main-header">🖼️ Conversor PNG → WEBP | PMCs SoftExpert</h1>', unsafe_allow_html=True)
    
    # Sidebar com configurações
    st.sidebar.header("⚙️ Configurações")
    
    # Opções de compressão
    compression_mode = st.sidebar.radio(
        "Modo de compressão:",
        ["Com perdas (menor tamanho)", "Sem perdas (melhor qualidade)"]
    )
    
    lossless = compression_mode == "Sem perdas (melhor qualidade)"
    
    if not lossless:
        quality = st.sidebar.slider("Qualidade da compressão:", 10, 100, 85, 5)
    else:
        quality = 100
    
    # Informações sobre o formato WEBP
    with st.sidebar.expander("ℹ️ Sobre o WEBP"):
        st.write("""
        **Vantagens do WEBP:**
        - Até 35% menor que PNG
        - Suporte a transparência
        - Melhor para web
        - Suportado pelos navegadores modernos
        
        **Qualidade recomendada:**
        - 80-85: Boa qualidade geral
        - 90-95: Alta qualidade
        - 70-80: Para reduzir mais o tamanho
        """)
    
    # Upload de arquivos
    st.header("📁 Enviar Imagens")
    uploaded_files = st.file_uploader(
        "Escolha as imagens PNG para converter:",
        type=['png'],
        accept_multiple_files=True,
        help="Você pode selecionar múltiplos arquivos PNG de uma vez"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")
        
        # Botão de conversão
        if st.button("🚀 Converter para WEBP", type="primary"):
            
            # Barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            converted_files = []
            all_stats = []
            total_original_size = 0
            total_new_size = 0
            
            # Processar cada arquivo
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Convertendo: {uploaded_file.name}")
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                # Ler dados do arquivo
                file_data = uploaded_file.read()
                
                # Converter
                webp_data, stats = convert_image_to_webp(
                    file_data, 
                    uploaded_file.name, 
                    quality, 
                    lossless
                )
                
                if webp_data and stats:
                    # Nome do arquivo convertido
                    webp_filename = uploaded_file.name.rsplit('.', 1)[0] + '.webp'
                    
                    converted_files.append((webp_data, webp_filename))
                    all_stats.append(stats)
                    total_original_size += stats['original_size']
                    total_new_size += stats['new_size']
            
            # Limpar barra de progresso
            progress_bar.empty()
            status_text.empty()
            
            if converted_files:
                st.success("🎉 Conversão concluída com sucesso!")
                
                # Estatísticas gerais
                total_reduction = (1 - total_new_size / total_original_size) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Arquivos convertidos", len(converted_files))
                with col2:
                    st.metric("Tamanho original", format_bytes(total_original_size))
                with col3:
                    st.metric("Tamanho final", format_bytes(total_new_size))
                with col4:
                    st.metric("Redução total", f"{total_reduction:.1f}%")
                
                # Tabela com detalhes de cada arquivo
                st.header("📊 Detalhes da Conversão")
                
                stats_data = []
                for stats in all_stats:
                    stats_data.append({
                        "Arquivo": stats['filename'],
                        "Dimensões": stats['dimensions'],
                        "Tamanho Original": format_bytes(stats['original_size']),
                        "Tamanho WEBP": format_bytes(stats['new_size']),
                        "Redução": f"{stats['reduction']:.1f}%",
                        "Compressão": stats['compression_type']
                    })
                
                st.dataframe(stats_data, use_container_width=True)
                
                # Downloads
                st.header("💾 Fazer Download")
                
                if len(converted_files) == 1:
                    # Download individual
                    webp_data, webp_filename = converted_files[0]
                    st.download_button(
                        label=f"📥 Baixar {webp_filename}",
                        data=webp_data,
                        file_name=webp_filename,
                        mime="image/webp"
                    )
                else:
                    # Download em ZIP
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for webp_data, webp_filename in converted_files:
                            zip_file.writestr(webp_filename, webp_data)
                    
                    st.download_button(
                        label=f"📦 Baixar todos os arquivos ({len(converted_files)} arquivos em ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="imagens_convertidas.zip",
                        mime="application/zip"
                    )
                
                # Preview das imagens (opcional)
                with st.expander("🔍 Visualizar Imagens Convertidas"):
                    cols = st.columns(min(3, len(converted_files)))
                    for i, (webp_data, webp_filename) in enumerate(converted_files):
                        with cols[i % 3]:
                            st.image(webp_data, caption=webp_filename, width=200)
    
    else:
        # Instruções quando não há arquivos
        st.info("""
        👆 **Como usar:**
        1. Clique no botão acima para fazer upload das suas imagens PNG
        2. Ajuste as configurações na barra lateral se necessário
        3. Clique em "Converter para WEBP"
        4. Faça o download dos arquivos convertidos
        
        💡 **Dica:** Você pode enviar múltiplos arquivos de uma vez!
        """)
    
    # Rodapé
    st.markdown("---")
    st.markdown(
        "🚀 **Conversor PNG → WEBP** | "
        "Desenvolvido para otimizar suas imagens para web"
    )

if __name__ == "__main__":
    main()
