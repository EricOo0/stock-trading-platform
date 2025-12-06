
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PDFParseTool:
    """
    PDF Parsing Tool
    Parses PDF to markdown using LlamaParse (primary) or PyMuPDF (fallback).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def parse(self, file_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Synchronously parse a PDF file.
        """
        try:
            if not os.path.exists(file_path):
                return {"status": "error", "error": f"File not found: {file_path}"}

            # Use instance key -> config/env -> None
            from tools.config import config
            api_key = self.api_key or config.get_api_key("llama_cloud")
            
            if not api_key:
                logger.warning("LLAMA_CLOUD_API_KEY not set, falling back to pymupdf")
                return self._fallback_parse(file_path)

            logger.info(f"Parsing PDF with LlamaParse: {file_path} with language: {language}")

            try:
                from llama_cloud_services import LlamaParse
                parser = LlamaParse(
                    api_key=api_key,
                    num_workers=4,
                    verbose=True,
                    language=language
                )

                # Parse the file
                result = parser.parse(file_path)

                # Extract markdown content
                content = ""
                if hasattr(result, "get_markdown_documents"):
                    markdown_documents = result.get_markdown_documents(split_by_page=True)
                    content = "\n\n".join([doc.text for doc in markdown_documents])
                elif isinstance(result, list):
                    content = "\n\n".join([doc.text for doc in result])
                else:
                    content = str(result)

                return {
                    "status": "success",
                    "content": content,
                    "file_path": file_path,
                    "method": "llama_parse"
                }
            except ImportError:
                 logger.warning("llama_cloud_services not installed, falling back.")
                 return self._fallback_parse(file_path)
            except Exception as e:
                logger.warning(f"LlamaParse failed: {e}, falling back to pymupdf")
                return self._fallback_parse(file_path)

        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _fallback_parse(self, file_path: str) -> Dict[str, Any]:
        """
        Fallback PDF parser using PyMuPDF (fitz)
        """
        try:
            import fitz  # PyMuPDF
            logger.info(f"Using PyMuPDF fallback for: {file_path}")
            
            doc = fitz.open(file_path)
            content = ""
            page_count = len(doc)
            
            for page_num in range(page_count):
                page = doc[page_num]
                content += f"--- Page {page_num + 1} ---\n"
                content += page.get_text() + "\n\n"
            
            doc.close()
            
            return {
                "status": "success",
                "content": content,
                "file_path": file_path,
                "method": "pymupdf_fallback",
                "pages": page_count
            }
            
        except ImportError:
            logger.error("PyMuPDF not installed, cannot use fallback")
            return {
                "status": "error",
                "error": "PyMuPDF not installed, cannot use fallback. Install with: pip install PyMuPDF"
            }
        except Exception as e:
            logger.error(f"PyMuPDF fallback failed: {str(e)}")
            return {
                "status": "error",
                "error": f"PyMuPDF fallback failed: {str(e)}"
            }

if __name__ == "__main__":
    tool = PDFParseTool()
    # print(tool.parse("test.pdf"))
