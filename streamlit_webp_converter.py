#!/usr/bin/env python3
"""
Conversor Universal → WEBP
Aplicação Streamlit para converter PNG, JPEG e GIF para WEBP
"""

import streamlit as st
import io
import zipfile
from PIL import Image, ImageSequence
import base64
from typing import List, Tuple

# Configuração da página
st.set_page_config(
    page_title="Conversor Universal → WEBP",
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
    Converte uma imagem para WEBP (suporta PNG, JPEG, GIF)
    
    Args:
        image_data: Dados da imagem em bytes
        filename: Nome do arquivo original
        quality: Qualidade da compressão (0-100)
        lossless: Se usar compressão sem perdas
    
    Returns:
        Tuple com os dados da imagem convertida e estatísticas
    """
    try:
        # Detectar tipo de arquivo
        file_ext = filename.lower().split('.')[-1]
        
        # Tratar GIF (verificar se é animado)
        if file_ext == 'gif':
            return convert_gif_to_webp(image_data, filename, quality, lossless)
        
        # Abrir imagem
        image = Image.open(io.BytesIO(image_data))
        
        # Converter para modo RGB se necessário
        if image.mode == 'RGBA':
            # Preservar transparência para PNG
            if file_ext == 'png':
                # Manter RGBA para preservar transparência
                pass
            else:
                # Para JPEG, criar fundo branco
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
        elif image.mode == 'P':
            # Converter paleta para RGBA se tiver transparência
            if 'transparency' in image.info:
                image = image.convert('RGBA')
            else:
                image = image.convert('RGB')
        elif image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        
        # Converter para WEBP
        output_buffer = io.BytesIO()
        
        if lossless:
            image.save(output_buffer, 'WEBP', lossless=True)
            compression_type = "Sem perdas"
        else:
            if image.mode == 'RGBA':
                # Para imagens com transparência, usar qualidade ligeiramente mais alta
                image.save(output_buffer, 'WEBP', quality=min(quality + 5, 100), optimize=True)
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
            'original_format': file_ext.upper(),
            'original_size': original_size,
            'new_size': new_size,
            'reduction': reduction,
            'compression_type': compression_type,
            'dimensions': f"{image.size[0]}x{image.size[1]}",
            'has_transparency': image.mode == 'RGBA'
        }
        
        return webp_data, stats
        
    except Exception as e:
        st.error(f"Erro ao converter {filename}: {str(e)}")
        return None, None

def convert_gif_to_webp(image_data: bytes, filename: str, quality: int, lossless: bool) -> Tuple[bytes, dict]:
    """
    Converte GIF para WEBP (animado se necessário, estático se for GIF estático)
    """
    try:
        gif_image = Image.open(io.BytesIO(image_data))
        
        # Verificar se é realmente animado
        is_animated = getattr(gif_image, 'is_animated', False)
        n_frames = getattr(gif_image, 'n_frames', 1)
        
        # Se é GIF animado (mais de 1 frame), converter para WEBP animado
        if is_animated and n_frames > 1:
            return convert_animated_gif_to_webp(gif_image, image_data, filename, quality, lossless)
        else:
            # GIF estático - converter para WEBP estático normal
            return convert_static_gif_to_webp(gif_image, image_data, filename, quality, lossless)
            
    except Exception as e:
        st.error(f"Erro ao processar GIF {filename}: {str(e)}")
        return None, None

def convert_static_gif_to_webp(gif_image: Image.Image, image_data: bytes, filename: str, quality: int, lossless: bool) -> Tuple[bytes, dict]:
    """
    Converte GIF estático para WEBP estático
    """
    try:
        # Converter para RGBA para preservar transparência
        if gif_image.mode == 'P':
            if 'transparency' in gif_image.info:
                gif_image = gif_image.convert('RGBA')
            else:
                gif_image = gif_image.convert('RGB')
        elif gif_image.mode not in ('RGB', 'RGBA'):
            gif_image = gif_image.convert('RGB')
        
        # Salvar como WEBP estático
        output_buffer = io.BytesIO()
        
        if lossless:
            gif_image.save(output_buffer, 'WEBP', lossless=True)
            compression_type = "WEBP Estático - Sem perdas"
        else:
            gif_image.save(output_buffer, 'WEBP', quality=quality, optimize=True)
            compression_type = f"WEBP Estático - Qualidade {quality}"
        
        webp_data = output_buffer.getvalue()
        
        # Calcular estatísticas
        original_size = len(image_data)
        new_size = len(webp_data)
        reduction = (1 - new_size / original_size) * 100
        
        stats = {
            'filename': filename,
            'original_format': 'GIF',
            'original_size': original_size,
            'new_size': new_size,
            'reduction': reduction,
            'compression_type': compression_type,
            'dimensions': f"{gif_image.size[0]}x{gif_image.size[1]}",
            'has_transparency': gif_image.mode == 'RGBA',
            'frames': 1,
            'animated': False,
            'output_type': 'WEBP Estático'
        }
        
        return webp_data, stats
        
    except Exception as e:
        st.error(f"Erro ao converter GIF estático {filename}: {str(e)}")
        return None, None

def convert_animated_gif_to_webp(gif_image: Image.Image, image_data: bytes, filename: str, quality: int, lossless: bool) -> Tuple[bytes, dict]:
    """
    Converte GIF animado para WEBP animado
    """
    try:
        # Extrair todos os frames e durações
        frames = []
        durations = []
        
        # Iterar por todos os frames
        for frame_index in range(gif_image.n_frames):
            gif_image.seek(frame_index)
            
            # Copiar o frame atual
            frame = gif_image.copy()
            
            # Converter para RGBA se necessário
            if frame.mode == 'P':
                # Se tem transparência, converter para RGBA
                if 'transparency' in frame.info:
                    frame = frame.convert('RGBA')
                else:
                    frame = frame.convert('RGB')
            elif frame.mode not in ('RGB', 'RGBA'):
                frame = frame.convert('RGBA')
            
            frames.append(frame)
            
            # Obter duração do frame (em milissegundos)
            duration = frame.info.get('duration', 100)
            # Garantir duração mínima para evitar animações muito rápidas
            duration = max(duration, 50)
            durations.append(duration)
        
        # Resetar para o primeiro frame
        gif_image.seek(0)
        
        # Salvar como WEBP animado
        output_buffer = io.BytesIO()
        
        if lossless:
            frames[0].save(
                output_buffer,
                'WEBP',
                save_all=True,
                append_images=frames[1:] if len(frames) > 1 else [],
                duration=durations,
                loop=0,  # Loop infinito
                lossless=True,
                optimize=True
            )
            compression_type = "WEBP Animado - Sem perdas"
        else:
            frames[0].save(
                output_buffer,
                'WEBP',
                save_all=True,
                append_images=frames[1:] if len(frames) > 1 else [],
                duration=durations,
                loop=0,  # Loop infinito
                quality=quality,
                optimize=True
            )
            compression_type = f"WEBP Animado - Qualidade {quality}"
        
        webp_data = output_buffer.getvalue()
        
        # Calcular estatísticas
        original_size = len(image_data)
        new_size = len(webp_data)
        reduction = (1 - new_size / original_size) * 100
        
        stats = {
            'filename': filename,
            'original_format': 'GIF',
            'original_size': original_size,
            'new_size': new_size,
            'reduction': reduction,
            'compression_type': compression_type,
            'dimensions': f"{gif_image.size[0]}x{gif_image.size[1]}",
            'has_transparency': any(frame.mode == 'RGBA' for frame in frames),
            'frames': len(frames),
            'animated': True,
            'output_type': 'WEBP Animado'
        }
        
        return webp_data, stats
        
    except Exception as e:
        st.error(f"Erro ao converter GIF animado {filename}: {str(e)}")
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
    st.markdown('<h1 class="main-header">🖼️ Conversor Universal → WEBP<b> PMCs Softexpert</b></h1>', unsafe_allow_html=True)
    
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
    
    # Informações sobre formatos suportados
    with st.sidebar.expander("📁 Formatos Suportados"):
        st.write("""
        **Entrada:** 
        - 🖼️ **PNG** - Imagens com transparência
        - 📷 **JPEG/JPG** - Fotografias
        - 🎬 **GIF** - Animações e imagens simples
        
        **Saída:**
        - 🚀 **WEBP** - Formato otimizado para web
        - 🎬 **WEBP Animado** - Para GIFs animados
        """)
    
    # Informações sobre o formato WEBP
    with st.sidebar.expander("ℹ️ Vantagens do WEBP"):
        st.write("""
        **Por que converter para WEBP:**
        - 📉 Até 35% menor que PNG
        - 📉 Até 25% menor que JPEG
        - 📉 Até 50% menor que GIF
        - ✨ Suporte a transparência
        - 🎬 Suporte a animações (melhor que GIF)
        - 🌐 Suportado por navegadores modernos
        - ⚡ Carregamento mais rápido
        
        **Qualidade recomendada:**
        - 📷 **Fotos**: 80-85
        - 🎨 **Gráficos**: 90-95  
        - 🎬 **GIFs**: 75-85 (animações)
        - 💾 **Economia**: 70-80
        """)
    
    # Informação sobre GIFs
    with st.sidebar.expander("🎬 Sobre GIFs → WEBP"):
        st.write("""
        **Conversão Inteligente de GIFs:**
        - 🎬 **GIF Animado** → **WEBP Animado**
        - 🖼️ **GIF Estático** → **WEBP Estático**
        - ✅ **Transparência preservada**
        - ✅ **Animações mantidas** com melhor compressão
        - ✅ **Até 50% menores** que GIF original
        - ✅ **Melhor qualidade** que GIF
        - ✅ **Suporte nativo** em navegadores modernos
        """)
    
    # Upload de arquivos
    st.header("📁 Enviar Imagens")
    uploaded_files = st.file_uploader(
        "Escolha as imagens para converter:",
        type=['png', 'jpg', 'jpeg', 'gif'],
        accept_multiple_files=True,
        help="Suporte a PNG, JPEG e GIF (incluindo animados)"
    )
    
    if uploaded_files:
        # Mostrar tipos de arquivo detectados
        file_types = {}
        for file in uploaded_files:
            ext = file.name.lower().split('.')[-1]
            if ext == 'jpg':
                ext = 'jpeg'
            file_types[ext.upper()] = file_types.get(ext.upper(), 0) + 1
        
        types_text = ", ".join([f"{count} {ftype}" for ftype, count in file_types.items()])
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s): {types_text}")
        
        # Mostrar preview dos arquivos
        with st.expander("🔍 Visualizar arquivos carregados"):
            cols = st.columns(min(4, len(uploaded_files)))
            for i, file in enumerate(uploaded_files):
                with cols[i % 4]:
                    try:
                        if file.type.startswith('image'):
                            st.image(file, caption=file.name, width=150)
                        else:
                            st.write(f"📁 {file.name}")
                    except:
                        st.write(f"📁 {file.name}")
        
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
                file_ext = uploaded_file.name.lower().split('.')[-1]
                status_text.text(f"Convertendo {file_ext.upper()}: {uploaded_file.name}")
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
                    row = {
                        "Arquivo": stats['filename'],
                        "Formato": stats['original_format'],
                        "Dimensões": stats['dimensions'],
                        "Tamanho Original": format_bytes(stats['original_size']),
                        "Tamanho WEBP": format_bytes(stats['new_size']),
                        "Redução": f"{stats['reduction']:.1f}%",
                        "Compressão": stats['compression_type']
                    }
                    
                    # Adicionar informações específicas para GIFs
                    if 'frames' in stats:
                        row["Frames"] = stats['frames']
                        row["Animado"] = "Sim" if stats.get('animated', False) else "Não"
                        if 'output_type' in stats:
                            row["Tipo Saída"] = stats['output_type']
                    
                    # Adicionar informação sobre transparência
                    if stats.get('has_transparency'):
                        row["Transparência"] = "Sim"
                    
                    stats_data.append(row)
                
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
                        file_name="imagens_convertidas_webp.zip",
                        mime="application/zip"
                    )
                
                # Preview das imagens convertidas
                with st.expander("🔍 Visualizar Imagens Convertidas"):
                    cols = st.columns(min(3, len(converted_files)))
                    for i, (webp_data, webp_filename) in enumerate(converted_files):
                        with cols[i % 3]:
                            st.image(webp_data, caption=webp_filename, width=200)
    
    else:
        # Instruções quando não há arquivos
        st.info("""
        👆 **Como usar:**
        1. **Faça upload** das suas imagens (PNG, JPEG, GIF)
        2. **Ajuste as configurações** na barra lateral se necessário
        3. **Clique em "Converter"** e aguarde o processamento
        4. **Faça download** dos arquivos WEBP otimizados
        
        💡 **Formatos suportados:**
        - 🖼️ **PNG** - Preserva transparência → WEBP estático
        - 📷 **JPEG/JPG** - Fotos e imagens → WEBP estático
        - 🎬 **GIF Animado** - **Vira WEBP Animado!**
        - 🖼️ **GIF Estático** - Vira WEBP estático
        
        ⚡ **Benefícios:**
        - Arquivos até **50% menores** (GIFs)
        - **Transparência preservada** (PNG/GIF)
        - **Animações mantidas** e melhoradas (GIF animado)
        - **Detecção automática** de GIFs animados vs estáticos
        - **Qualidade ajustável**
        """)
    
    # Rodapé
    st.markdown("---")
    st.markdown(
        "🚀 **Conversor Universal → WEBP** | "
        "PNG • JPEG • GIF → WEBP otimizado para web | "
        "🎬 **GIFs animados preservam movimento!**"
    )

if __name__ == "__main__":
    main()
