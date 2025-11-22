"""
Test script for Cloudinary document upload endpoint
"""
import requests
import base64
import json
import sys
import os

# Default server URL
BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/documents/upload"


def test_upload_base64(file_path: str, filename: str = None, folder: str = None):
    """
    Test the base64 upload endpoint
    
    Args:
        file_path: Path to the file to upload
        filename: Optional filename (defaults to file name from path)
        folder: Optional Cloudinary folder
    """
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return
    
    # Get filename if not provided
    if not filename:
        filename = os.path.basename(file_path)
    
    print(f"📄 Reading file: {file_path}")
    print(f"📝 Filename: {filename}")
    
    # Read and encode file to base64
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
        
        print(f"✅ File encoded to base64 ({len(file_base64)} characters)")
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return
    
    # Prepare request payload
    payload = {
        "file_base64": file_base64,
        "filename": filename,
        "resource_type": "auto"
    }
    
    if folder:
        payload["folder"] = folder
    
    print(f"\n🚀 Uploading to: {ENDPOINT}")
    print(f"📦 Payload size: {len(json.dumps(payload))} bytes")
    
    # Make request
    try:
        response = requests.post(
            ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Upload Successful!")
            print(f"   URL: {result.get('url')}")
            print(f"   Public ID: {result.get('public_id')}")
            print(f"   Format: {result.get('format')}")
            print(f"   Size: {result.get('bytes')} bytes")
            print(f"   Resource Type: {result.get('resource_type')}")
            return result
        else:
            print(f"\n❌ Upload Failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Could not connect to server at {BASE_URL}")
        print("   Make sure the FastAPI server is running!")
        return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def test_upload_with_data_uri(file_path: str, filename: str = None, folder: str = None):
    """
    Test upload with data URI format (data:mime/type;base64,...)
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return
    
    if not filename:
        filename = os.path.basename(file_path)
    
    # Determine MIME type from extension
    ext = os.path.splitext(filename)[1].lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain'
    }
    mime_type = mime_types.get(ext, 'application/octet-stream')
    
    print(f"📄 Reading file: {file_path}")
    print(f"📝 Filename: {filename}")
    print(f"🔖 MIME Type: {mime_type}")
    
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            base64_content = base64.b64encode(file_bytes).decode('utf-8')
            file_base64 = f"data:{mime_type};base64,{base64_content}"
        
        print(f"✅ File encoded to base64 with data URI prefix")
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return
    
    payload = {
        "file_base64": file_base64,
        "filename": filename,
        "resource_type": "auto"
    }
    
    if folder:
        payload["folder"] = folder
    
    print(f"\n🚀 Uploading to: {ENDPOINT}")
    
    try:
        response = requests.post(
            ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Upload Successful!")
            print(f"   URL: {result.get('url')}")
            print(f"   Public ID: {result.get('public_id')}")
            return result
        else:
            print(f"\n❌ Upload Failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Cloudinary Document Upload Test")
    print("=" * 60)
    
    # Check if file path provided as argument
    if len(sys.argv) < 2:
        print("\nUsage:")
        print(f"  python test_cloudinary_upload.py <file_path> [filename] [folder]")
        print("\nExample:")
        print(f"  python test_cloudinary_upload.py document.pdf")
        print(f"  python test_cloudinary_upload.py document.pdf my_doc.pdf tuition_master/test")
        print("\nOr test with a sample file:")
        
        # Try to find a test file
        test_files = [
            "../A Brief History of India_text.pdf",
            "test.pdf",
            "test.txt"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                print(f"\n📋 Found test file: {test_file}")
                print(f"   Running test...\n")
                test_upload_base64(test_file, folder="tuition_master/test")
                sys.exit(0)
        
        print("\n   No test files found. Please provide a file path.")
        sys.exit(1)
    
    file_path = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    folder = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Test regular base64 upload
    print("\n" + "=" * 60)
    print("Test 1: Regular Base64 Upload")
    print("=" * 60)
    result1 = test_upload_base64(file_path, filename, folder)
    
    # Test data URI format upload
    print("\n" + "=" * 60)
    print("Test 2: Data URI Format Upload")
    print("=" * 60)
    result2 = test_upload_with_data_uri(file_path, filename, folder)
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

