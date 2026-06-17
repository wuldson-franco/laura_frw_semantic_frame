#%%
%pip install bs4 selenium webdriver-manager
#%%
import os
import time
import re
import json
import base64
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
#%%
def ler_csv(csv_path):
    """Lê o CSV e retorna lista de (numero_sei, url)"""
    processos = []
    with open(csv_path, encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            partes = linha.split(' - ', 1)
            if len(partes) != 2:
                continue
            numero_sei, url = partes
            processos.append((numero_sei.strip(), url.strip()))
    return processos

class SEIDownloaderSelenium:
    def __init__(self, base_url, numero_processo, base_dir=r'D:\WULDSON\Estudos\Mestrado\IFPB\Disciplinas\orientacao\Transparencia_IA\projeto_anatel\dados\pdfs_anatel'):
        self.base_url = base_url
        self.numero_processo = numero_processo
        self.driver = None

        # Converte número do processo para nome de pasta
        # Ex: 53500.014139/2023-61 → 53500.014139_2023-61
        nome_pasta = numero_processo.replace('/', '_').replace('.', '.', 1)
        # Garante formato correto: 53500.014139_2023-61
        nome_pasta = re.sub(r'[<>:"/\\|?*]', '_', numero_processo)
        nome_pasta = nome_pasta.replace('/', '_')

        self.download_dir = os.path.join(base_dir, nome_pasta)
        os.makedirs(self.download_dir, exist_ok=True)
        print(f'Pasta de destino: {self.download_dir}')
        
    def setup_driver(self, headless=False):
        """Configura o Chrome WebDriver com configurações de download"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Habilita modo de impressão para PDF
        chrome_options.add_argument('--kiosk-printing')
        
        # Configurações para download automático de PDFs
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "plugins.plugins_disabled": ["Chrome PDF Viewer"],
            "printing.print_preview_sticky_settings.appState": json.dumps({
                "recentDestinations": [{
                    "id": "Save as PDF",
                    "origin": "local",
                    "account": ""
                }],
                "selectedDestinationId": "Save as PDF",
                "version": 2
            })
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Usa webdriver-manager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver
    
    def wait_for_download(self, timeout=30):
        """Aguarda o download ser concluído"""
        seconds = 0
        download_dir = Path(self.download_dir)
        
        while seconds < timeout:
            time.sleep(1)
            # Verifica se há arquivos .crdownload (download em andamento)
            downloading = list(download_dir.glob('*.crdownload'))
            if not downloading:
                # Verifica se há novos arquivos
                files = list(download_dir.glob('*'))
                if files:
                    return True
            seconds += 1
        return False
    
    def get_latest_download(self):
        """Retorna o arquivo mais recentemente baixado"""
        download_dir = Path(self.download_dir)
        files = list(download_dir.glob('*'))
        if not files:
            return None
        latest = max(files, key=lambda x: x.stat().st_mtime)
        return latest
    
    def print_page_to_pdf(self, filename):
        """Imprime a página atual como PDF usando Chrome DevTools Protocol"""
        try:
            # Aguarda página carregar completamente
            time.sleep(2)
            
            # Usa o Chrome DevTools Protocol para imprimir
            result = self.driver.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True,
                "landscape": False,
                "paperWidth": 8.27,  # A4
                "paperHeight": 11.69,
                "marginTop": 0.4,
                "marginBottom": 0.4,
                "marginLeft": 0.4,
                "marginRight": 0.4,
                "displayHeaderFooter": False,
                "preferCSSPageSize": True,
                "generateTaggedPDF": False,
                "generateDocumentOutline": False
            })
            
            # Decodifica o PDF em base64
            pdf_data = base64.b64decode(result['data'])
            
            # Salva o PDF
            filepath = os.path.join(self.download_dir, filename)
            
            # Evita sobrescrever
            counter = 1
            base_filepath = filepath
            while os.path.exists(filepath):
                name, ext = os.path.splitext(base_filepath)
                filepath = f"{name}_{counter}{ext}"
                counter += 1
            
            with open(filepath, 'wb') as f:
                f.write(pdf_data)
            
            return filepath
            
        except Exception as e:
            print(f"    ⚠ Erro ao converter para PDF: {str(e)}")
            return None
    
    def rename_downloaded_file(self, new_name):
        """Renomeia o último arquivo baixado"""
        latest = self.get_latest_download()
        if latest and latest.exists():
            new_path = latest.parent / new_name
            # Evita sobrescrever
            counter = 1
            while new_path.exists():
                name_parts = new_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_path = latest.parent / f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    new_path = latest.parent / f"{new_name}_{counter}"
                counter += 1
            
            latest.rename(new_path)
            return new_path
        return None
    
    def sanitize_filename(self, filename):
        """Remove caracteres inválidos do nome do arquivo"""
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip()
        return filename[:200]
    
    def is_pdf_url(self, url):
        """Verifica se a URL é de um PDF"""
        return url and '.pdf' in url.lower()
    
    def detect_content_type(self):
        """Detecta se o conteúdo atual é PDF ou HTML"""
        try:
            current_url = self.driver.current_url
            
            # Verifica pela URL
            if '.pdf' in current_url.lower():
                return 'pdf'
            
            # Verifica pelo conteúdo da página
            page_source = self.driver.page_source[:1000].lower()
            
            if 'application/pdf' in page_source or '<embed' in page_source:
                return 'pdf'
            
            # Se tem muito HTML, provavelmente é página HTML
            if '<html' in page_source or '<body' in page_source:
                return 'html'
            
            return 'unknown'
            
        except:
            return 'unknown'
    
    def find_document_links(self):
        """Encontra elementos clicáveis de documentos"""
        print("\nProcurando documentos na página...\n")
        self.driver.get(self.base_url)
        
        # Aguarda carregamento
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)
        
        document_elements = []
        
        try:
            all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            
            for link in all_links:
                try:
                    text = link.text.strip()
                    href = link.get_attribute('href')
                    onclick = link.get_attribute('onclick')
                    
                    # Identifica links de documentos
                    if text and (text.isdigit() or 
                                (href and 'javascript' in href) or 
                                onclick):
                        parent = link.find_element(By.XPATH, '..')
                        if parent.tag_name in ['td', 'div']:
                            document_elements.append({
                                'element': link,
                                'text': text,
                                'href': href,
                                'onclick': onclick
                            })
                except:
                    continue
                    
        except Exception as e:
            print(f"Erro ao buscar documentos: {e}")
        
        # Remove duplicatas
        seen = set()
        unique_docs = []
        for doc in document_elements:
            if doc['text'] not in seen and doc['text']:
                seen.add(doc['text'])
                unique_docs.append(doc)
        
        print(f"✓ Encontrados {len(unique_docs)} documentos únicos\n")
        
        if unique_docs:
            print("Documentos encontrados:")
            for i, doc in enumerate(unique_docs[:10], 1):
                print(f"{i}. Documento: {doc['text']}")
            if len(unique_docs) > 10:
                print(f"... e mais {len(unique_docs) - 10} documentos")
        
        return unique_docs
    
    def click_and_download(self, doc_info, index, total):
        """Clica no documento e faz download (PDF direto ou converte HTML para PDF)"""
        try:
            doc_name = doc_info['text']
            print(f"\n[{index}/{total}] Processando: {doc_name}")
            
            # Guarda janela original
            original_window = self.driver.current_window_handle
            files_before = set(Path(self.download_dir).glob('*'))
            
            # Clica no elemento
            element = doc_info['element']
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            try:
                element.click()
            except:
                self.driver.execute_script("arguments[0].click();", element)
            
            time.sleep(2)
            
            # Verifica se abriu nova janela/aba
            windows = self.driver.window_handles
            if len(windows) > 1:
                # Muda para nova janela
                self.driver.switch_to.window(windows[-1])
                time.sleep(2)
                
                # Detecta tipo de conteúdo
                content_type = self.detect_content_type()
                print(f"  📄 Tipo detectado: {content_type}")
                
                if content_type == 'pdf':
                    # É PDF - aguarda download
                    print("  ⏳ Aguardando download do PDF...")
                    if self.wait_for_download(timeout=30):
                        files_after = set(Path(self.download_dir).glob('*'))
                        new_files = files_after - files_before
                        
                        if new_files:
                            new_file = list(new_files)[0]
                            ext = new_file.suffix
                            new_name = self.sanitize_filename(f"doc_{doc_name}{ext}")
                            renamed = self.rename_downloaded_file(new_name)
                            
                            if renamed:
                                size = renamed.stat().st_size
                                print(f"  ✓ Baixado: {renamed.name} ({size:,} bytes)")
                            else:
                                print(f"  ✓ Baixado: {new_file.name}")
                            
                            # Fecha janela e volta
                            self.driver.close()
                            self.driver.switch_to.window(original_window)
                            return True
                
                elif content_type == 'html':
                    # É HTML - converte para PDF
                    print("  🔄 Convertendo HTML para PDF...")
                    
                    filename = self.sanitize_filename(f"doc_{doc_name}.pdf")
                    pdf_path = self.print_page_to_pdf(filename)
                    
                    if pdf_path:
                        size = os.path.getsize(pdf_path)
                        print(f"  ✓ Convertido e salvo: {os.path.basename(pdf_path)} ({size:,} bytes)")
                        
                        # Fecha janela e volta
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                        return True
                    else:
                        print("  ✗ Falha na conversão")
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                        return False
                
                else:
                    print("  ⚠ Tipo de conteúdo não reconhecido")
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
                    return False
            
            else:
                # Não abriu nova janela - pode ter baixado direto
                print("  ⏳ Aguardando download...")
                if self.wait_for_download(timeout=30):
                    files_after = set(Path(self.download_dir).glob('*'))
                    new_files = files_after - files_before
                    
                    if new_files:
                        new_file = list(new_files)[0]
                        ext = new_file.suffix
                        new_name = self.sanitize_filename(f"doc_{doc_name}{ext}")
                        renamed = self.rename_downloaded_file(new_name)
                        
                        if renamed:
                            size = renamed.stat().st_size
                            print(f"  ✓ Baixado: {renamed.name} ({size:,} bytes)")
                        else:
                            print(f"  ✓ Baixado: {new_file.name}")
                        return True
                
                print("  ⚠ Download não detectado")
                return False
                
        except Exception as e:
            print(f"  ✗ Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            # Tenta voltar para janela original
            try:
                self.driver.switch_to.window(original_window)
            except:
                pass
            return False
    
    def download_all(self):
        """Baixa todos os documentos encontrados"""
        try:
            print("="*70)
            print("DOWNLOADER DE DOCUMENTOS SEI - ANATEL")
            print("Com suporte para conversão HTML → PDF")
            print("="*70)
            
            self.setup_driver(headless=False)
            
            # Busca documentos
            documents = self.find_document_links()
            
            if not documents:
                print("\n⚠ Nenhum documento encontrado!")
                return
            
            print(f"\n{'='*70}")
            print(f"Diretório de download: {self.download_dir}")
            print(f"Total de documentos: {len(documents)}")
            print(f"{'='*70}\n")
            
            input("Pressione ENTER para iniciar o download...")
            
            # Download
            success = 0
            failed = 0
            
            for i, doc in enumerate(documents, 1):
                if self.click_and_download(doc, i, len(documents)):
                    success += 1
                else:
                    failed += 1
                
                # Pausa entre downloads
                if i < len(documents):
                    time.sleep(2)
            
            # Relatório
            print(f"\n{'='*70}")
            print("RELATÓRIO FINAL")
            print(f"{'='*70}")
            print(f"✓ Sucessos: {success}")
            print(f"✗ Falhas: {failed}")
            print(f"📁 Arquivos salvos em: {self.download_dir}")
            
            # Lista arquivos baixados
            files = sorted(list(Path(self.download_dir).glob('*')))
            if files:
                print(f"\nArquivos baixados ({len(files)}):")
                for f in files:
                    size = f.stat().st_size
                    print(f"  - {f.name} ({size:,} bytes)")
            
            print(f"{'='*70}")
            
        except Exception as e:
            print(f"\n✗ Erro durante execução: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                input("\nPressione ENTER para fechar o navegador...")
                self.driver.quit()
#%%

# Execução
if __name__ == "__main__":
    CSV_PATH = r'processo_documento_relacao.csv'
    BASE_DIR = r'D:\WULDSON\Estudos\Mestrado\IFPB\Disciplinas\orientacao\Transparencia_IA\projeto_anatel\dados\pdfs_anatel'

    processos = ler_csv(CSV_PATH)
    print(f'{len(processos)} processos encontrados no CSV\n')

    for i, (numero_sei, url) in enumerate(processos, 1):
        # Pula se pasta já existe com arquivos
        nome_pasta = re.sub(r'[<>:"/\\|?*]', '_', numero_sei).replace('/', '_')
        pasta = os.path.join(BASE_DIR, nome_pasta)
        if os.path.exists(pasta) and any(Path(pasta).glob('*')):
            print(f'[{i}/{len(processos)}] {numero_sei} — SKIP (já baixado)')
            continue

        print(f'[{i}/{len(processos)}] {numero_sei}')
        downloader = SEIDownloaderSelenium(url, numero_sei, base_dir=BASE_DIR)
        downloader.download_all()
        print(f'[{i}/{len(processos)}] {numero_sei} — OK ✓\n')
# %%
