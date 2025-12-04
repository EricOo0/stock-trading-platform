import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.pdf_parsing_tool.skill import PDFParsingSkill

# Load environment variables
load_dotenv()

def test_sync_parsing():
    print("\nTesting Sync Parsing...")
    skill = PDFParsingSkill()
    
    # Check for API key
    os.environ["LLAMA_CLOUD_API_KEY"] = "llx-vut3GxGTYhNpG6wPh8N3yj9LMpNRG158XZ2BLzcDjg8Vsu9y"
    if not os.getenv("LLAMA_CLOUD_API_KEY"):
        print("Skipping test: LLAMA_CLOUD_API_KEY not set")
        return

    # Create a dummy PDF file for testing if one doesn't exist
    test_file = "skills/pdf_parsing_tool/1224770636.pdf"
    if not os.path.exists(test_file):
        # We can't easily create a valid PDF without a library, so we'll check if a file is provided
        # Or we can try to parse a non-existent file to check error handling
        print(f"Test file {test_file} not found. Testing error handling for missing file.")
        result = skill._run("non_existent_file.pdf")
        print(f"Result for missing file: {result}")
        assert result["status"] == "error"
        assert "File not found" in result["error"]
    else:
        result = skill._fallback_parse(test_file)
        print(f"Result status: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"Content preview: {result.get('content')[:200]}...")
        else:
            print(f"Error: {result.get('error')}")

async def test_async_parsing():
    print("\nTesting Async Parsing...")
    skill = PDFParsingSkill()
    
    if not os.getenv("LLAMA_CLOUD_API_KEY"):
        print("Skipping test: LLAMA_CLOUD_API_KEY not set")
        return

    test_file = "test_document.pdf"
    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found. Testing error handling for missing file.")
        result = await skill._arun("non_existent_file.pdf")
        print(f"Result for missing file: {result}")
        assert result["status"] == "error"
    else:
        result = await skill._arun(test_file)
        print(f"Result status: {result.get('status')}")
        if result.get('status') == 'success':
            print(f"Content preview: {result.get('content')[:200]}...")
        else:
            print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    print("Starting PDF Parsing Tool Tests")
    test_sync_parsing()
    asyncio.run(test_async_parsing())
