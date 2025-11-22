"""
Script to encode a file to base64 for Cloudinary upload
"""
import base64
import sys
import os

def encode_file_to_base64(file_path):
    """
    Encode a file to base64 string
    
    Args:
        file_path: Path to the file to encode
    
    Returns:
        str: Base64 encoded string
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return None
    
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            base64_string = base64.b64encode(file_bytes).decode('utf-8')
        
        print(f"✅ File encoded successfully!")
        print(f"📄 File: {file_path}")
        print(f"📊 File size: {len(file_bytes)} bytes")
        print(f"📏 Base64 length: {len(base64_string)} characters")
        print(f"\n{'='*60}")
        print("BASE64 STRING:")
        print(f"{'='*60}\n")
        print(base64_string)
        print(f"\n{'='*60}\n")
        
        return base64_string
    except Exception as e:
        print(f"❌ Error encoding file: {str(e)}")
        return None


def create_postman_json(base64_string, filename, folder=None):
    """
    Create a Postman-ready JSON payload
    
    Args:
        base64_string: Base64 encoded file content
        filename: Original filename
        folder: Optional Cloudinary folder
    
    Returns:
        dict: JSON payload
    """
    payload = {
        "fileUrl": base64_string,
        "filename": filename,
        "resource_type": "auto"
    }
    
    if folder:
        payload["folder"] = folder
    
    return payload


if __name__ == "__main__":
    print("=" * 60)
    print("File to Base64 Encoder")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print(f"  python encode_to_base64.py <file_path> [filename] [folder]")
        print("\nExample:")
        print(f"  python encode_to_base64.py document.pdf")
        print(f"  python encode_to_base64.py document.pdf my_doc.pdf tuition_master/test")
        print("\nOr encode a specific file:")
        
        # Try to find common test files
        test_files = [
            "../A Brief History of India_text.pdf",
            "test.pdf",
            "test.txt"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                print(f"\n📋 Found test file: {test_file}")
                print(f"   Encoding...\n")
                base64_str = encode_file_to_base64(test_file)
                if base64_str:
                    filename = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(test_file)
                    folder = sys.argv[3] if len(sys.argv) > 3 else None
                    payload = create_postman_json(base64_str, filename, folder)
                    
                    print("\n" + "=" * 60)
                    print("POSTMAN JSON PAYLOAD:")
                    print("=" * 60)
                    import json
                    print(json.dumps(payload, indent=2))
                sys.exit(0)
        
        print("\n   No test files found. Please provide a file path.")
        sys.exit(1)
    
    file_path = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(file_path)
    folder = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Encode file
    base64_str = encode_file_to_base64(file_path)
    
    if base64_str:
        # Create Postman JSON
        payload = create_postman_json(base64_str, filename, folder)
        
        print("\n" + "=" * 60)
        print("POSTMAN JSON PAYLOAD:")
        print("=" * 60)
        import json
        print(json.dumps(payload, indent=2))
        
        # Save to file
        output_file = "postman_payload.json"
        with open(output_file, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"\n💾 Payload saved to: {output_file}")

