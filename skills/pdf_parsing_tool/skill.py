import os
import logging
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from llama_cloud_services import LlamaParse

# Configure logging
logger = logging.getLogger(__name__)

class PDFParsingInput(BaseModel):
    file_path: str = Field(description="The absolute path to the PDF file to be parsed.")
    language: Optional[str] = Field(default="en", description="The language of the document (e.g., 'en', 'zh'). Default is 'en'.")

class PDFParsingSkill(BaseTool):
    name: str = "pdf_parsing_tool"
    description: str = "Parses a PDF file and extracts its content as markdown using LlamaParse. Useful for reading and understanding PDF documents."
    args_schema: Type[BaseModel] = PDFParsingInput

    def _run(self, file_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Synchronously parse a PDF file.
        """
        try:
            api_key = os.getenv("LLAMA_CLOUD_API_KEY")
            if not api_key:
                logger.warning("LLAMA_CLOUD_API_KEY not set, falling back to pypdf")
                return self._fallback_parse(file_path)

            if not os.path.exists(file_path):
                return {
                    "status": "error",
                    "error": f"File not found: {file_path}"
                }

            logger.info(f"Parsing PDF file: {file_path} with language: {language}")

            try:
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
            except Exception as e:
                logger.warning(f"LlamaParse failed: {e}, falling back to pypdf")
                return self._fallback_parse(file_path)

        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _arun(self, file_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Asynchronously parse a PDF file.
        """
        try:
            api_key = os.getenv("LLAMA_CLOUD_API_KEY")
            if not api_key:
                 logger.warning("LLAMA_CLOUD_API_KEY not set, falling back to pypdf")
                 return self._fallback_parse(file_path)

            if not os.path.exists(file_path):
                return {
                    "status": "error",
                    "error": f"File not found: {file_path}"
                }

            logger.info(f"Async parsing PDF file: {file_path} with language: {language}")

            try:
                parser = LlamaParse(
                    api_key=api_key,
                    num_workers=4,
                    verbose=True,
                    language=language
                )

                # Async parse
                result = await parser.aparse(file_path)

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
            except Exception as e:
                logger.warning(f"LlamaParse async failed: {e}, falling back to pypdf")
                return self._fallback_parse(file_path)

        except Exception as e:
            logger.error(f"Error parsing PDF asynchronously: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _fallback_parse(self, file_path: str) -> Dict[str, Any]:
        """
        Fallback PDF parser using PyMuPDF (fitz)
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Parsed content dictionary
        """
        try:
            import fitz  # PyMuPDF
            logger.info(f"Using PyMuPDF fallback for: {file_path}")
            
            # Open PDF
            doc = fitz.open(file_path)
            content = ""
            page_count = len(doc)
            
            # Extract text from each page
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
