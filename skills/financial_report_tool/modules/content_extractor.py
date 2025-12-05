import requests
import os
import io
import hashlib
from typing import Tuple, Dict, Any
from loguru import logger
from bs4 import BeautifulSoup

def get_html_content(url: str, symbol: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Fetch HTML content, inject anchors, save locally, and return text/map.
    """
    try:
        headers = {
            "User-Agent": "StockAnalysisAgent/1.0 (admin@stockanalysis.com)"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding # Fix encoding issues
        
        html_content = response.text
        return save_html_content(html_content, symbol, url)
        
    except Exception as e:
        logger.error(f"Error processing HTML from {url}: {e}")
        return "", "", {}

def save_html_content(html_content: str, symbol: str, source_url: str = "") -> Tuple[str, str, Dict[str, Any]]:
    """
    Process HTML content: inject anchors, save locally, and return metadata.
    """
    try:
        logger.info(f"Processing HTML content for {symbol}. Source URL: {source_url}")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Handle relative links (images, css, etc) if source_url provided
        if source_url:
            # Handle special SEC viewer URL: https://www.sec.gov/ix?doc=/Archives/...
            if 'ix?doc=' in source_url:
                # Extract the actual path from the query param
                try:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(source_url)
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'doc' in params:
                        real_path = params['doc'][0]
                        # Ensure it starts with / if relative to domain
                        if not real_path.startswith('/'):
                             real_path = '/' + real_path
                        # Construct the full URL to the document
                        source_url = f"https://www.sec.gov{real_path}"
                        logger.info(f"Resolved IX URL to: {source_url}")
                except Exception as e:
                    logger.warning(f"Error parsing IX URL: {e}")

            # Determine base_url correctly
            if source_url.endswith('/'):
                base_url = source_url
            else:
                # Check if it looks like a file (has extension)
                path = source_url.split('?')[0]
                filename = path.split('/')[-1]
                # If it has an extension, strip it
                if '.' in filename:
                    base_url = source_url.rsplit('/', 1)[0]
                else:
                    base_url = source_url
            
            # Ensure base_url ends with / for <base> tag
            if not base_url.endswith('/'):
                base_url += '/'
                
            logger.info(f"Calculated Base URL: {base_url}")

            # Inject <base> tag
            if not soup.head:
                head = soup.new_tag('head')
                if soup.body:
                    soup.body.insert_before(head)
                else:
                    soup.insert(0, head)
            
            # Remove existing base tags
            for base in soup.head.find_all('base'):
                base.decompose()
                
            base_tag = soup.new_tag('base', href=base_url)
            soup.head.insert(0, base_tag)
            
            # Update img src - ONLY fix leading slash images which ignore <base>
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and src.startswith('/'):
                    img['src'] = f"https://www.sec.gov{src}"
                    
            # Note: We do NOT touch relative URLs anymore, trusting <base> tag

        # Remove scripts
        for script in soup(["script"]):
            script.decompose()
        
        # Add CSS for highlighting target anchor
        style_tag = soup.new_tag('style')
        style_tag.string = """
        :target {
            background-color: #fff3cd !important;
            border-left: 4px solid #ffc107 !important;
            transition: all 0.3s ease;
            padding: 4px;
            display: block;
            scroll-margin-top: 20px;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        """
        
        # Ensure meta charset is utf-8
        if not soup.head:
            head = soup.new_tag('head')
            if soup.body:
                soup.body.insert_before(head)
            else:
                soup.insert(0, head)
        
        # Remove existing charset meta if any to avoid duplicates/conflicts
        for meta in soup.head.find_all('meta', charset=True):
            meta.decompose()
        for meta in soup.head.find_all('meta', attrs={'http-equiv': 'Content-Type'}):
            meta.decompose()
            
        # Add new utf-8 meta
        meta_tag = soup.new_tag('meta', charset='utf-8')
        soup.head.insert(0, meta_tag)
        
        # Append style tag
        soup.head.append(style_tag)
            
        anchor_map = {}
        full_text = ""
        para_count = 0
        
        # Find all paragraphs, headers, and tables
        elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'table'])
        
        for elem in elements:
            text = elem.get_text(strip=True)
            if len(text) < 10: # Skip very short/empty elements
                continue
                
            # Check if this element is already processed (e.g. div containing p)
            if elem.name == 'div':
                # If div has block children, skip (let children handle it)
                if elem.find(['p', 'div', 'h1', 'h2', 'h3', 'li', 'table']):
                    continue
            
            # Special handling for tables
            if elem.name == 'table':
                pass

            anchor_id = f"html_{para_count}"
            # Inject ID into the HTML element
            elem['id'] = anchor_id
            
            anchor_map[anchor_id] = {
                "type": "html",
                "id": anchor_id,
                "content": text[:50] + "..."
            }
            
            full_text += f"[{anchor_id}] {text}\n\n"
            para_count += 1
            
        # Save modified HTML
        # Use 3 levels up for backend
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
        static_dir = os.path.join(backend_dir, "static", "reports")
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            
        content_hash = hashlib.md5(html_content[:1000].encode('utf-8')).hexdigest()[:10]
        filename = f"{symbol}_{content_hash}.html"
        file_path = os.path.join(static_dir, filename)
        
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(str(soup))
            
        local_url = f"http://localhost:8000/static/reports/{filename}"
        
        return full_text, local_url, anchor_map
        
    except Exception as e:
        logger.error(f"Error saving HTML content for {symbol}: {e}")
        return "", "", {}

def download_and_parse_pdf(url: str, symbol: str = "report") -> Tuple[str, str, Dict[str, Any]]:
    """
    Download PDF, save locally, and extract text with coordinates using PyMuPDF.
    Returns: (text_content, local_url, anchor_map)
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        
        pdf_content = response.content
        
        # Save PDF locally
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
        static_dir = os.path.join(backend_dir, "static", "reports")
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            
        file_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        filename = f"{symbol}_{file_hash}.pdf"
        file_path = os.path.join(static_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(pdf_content)
        
        # Local URL for frontend
        local_url = f"http://localhost:8000/static/reports/{filename}"
        
        import fitz  # PyMuPDF
        
        anchor_map = {}
        full_text = ""
        
        with io.BytesIO(pdf_content) as f:
            doc = fitz.open(stream=f, filetype="pdf")
            
            # Read first 50 pages max
            max_pages = min(len(doc), 50)
            
            for page_num in range(max_pages):
                page = doc[page_num]
                # Get text blocks with coordinates
                blocks = page.get_text("blocks")
                
                for block_idx, block in enumerate(blocks):
                    # block format: (x0, y0, x1, y1, "text", block_no, block_type)
                    if len(block) < 5:
                        continue
                        
                    x0, y0, x1, y1 = block[0], block[1], block[2], block[3]
                    text_content = block[4].strip()
                    
                    if not text_content:
                        continue
                        
                    anchor_id = f"pdf_{page_num + 1}_{block_idx}"
                    
                    anchor_map[anchor_id] = {
                        "type": "pdf",
                        "page": page_num + 1,
                        "rect": [x0, y0, x1, y1],
                        "content": text_content[:50] + "..." # Preview
                    }
                    
                    # Append to full text with anchor marker
                    full_text += f"[{anchor_id}] {text_content}\n\n"
                    
            doc.close()
            
        return full_text, local_url, anchor_map
        
    except Exception as e:
        logger.error(f"Error parsing PDF from {url}: {e}")
        return "", "", {}

def extract_sec_report_url(index_url: str) -> str:
    """
    Parse SEC index page to find the main report document URL (e.g., .htm file).
    """
    try:
        headers = {
            "User-Agent": "StockAnalysisAgent/1.0 (admin@stockanalysis.com)"
        }
        response = requests.get(index_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', {'summary': 'Document Format Files'})
        if not table:
            table = soup.find('table', {'class': 'tableFile'})
        
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    doc_type = cols[3].get_text(strip=True)
                    doc_name = cols[2].get_text(strip=True)
                    link = cols[2].find('a')
                    
                    if link and (doc_name.endswith('.htm') or doc_name.endswith('.html')):
                        href = link.get('href')
                        if href.startswith('/'):
                            return f"https://www.sec.gov{href}"
                        else:
                            # Determine base_url correctly
                            if index_url.endswith('/'):
                                base_url = index_url
                            else:
                                path = index_url.split('?')[0]
                                filename = path.split('/')[-1]
                                if '.' in filename:
                                    base_url = index_url.rsplit('/', 1)[0]
                                else:
                                    base_url = index_url
                            
                            if not base_url.endswith('/'):
                                base_url += '/'
                                
                            return f"{base_url}{href}"
                            
        return index_url
        
    except Exception as e:
        logger.error(f"Error extracting SEC report URL from {index_url}: {e}")
        return index_url
