# Cloudinary Setup Guide

This guide explains how to set up and use Cloudinary for document storage in the Tuition Master backend.

## Prerequisites

1. Create a Cloudinary account at https://cloudinary.com (free tier available)
2. Get your Cloudinary credentials from the dashboard:
   - Cloud Name
   - API Key
   - API Secret

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

This will install:
- `cloudinary==1.41.0` - Cloudinary Python SDK
- `python-multipart==0.0.9` - Required for file uploads in FastAPI

## Configuration

Add the following environment variables to your `.env` file:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## API Endpoints

### 1. Upload Document (Base64 Encoded) ⭐ **PRIMARY ENDPOINT**

**Endpoint:** `POST /api/documents/upload`

**Description:** Upload a base64 encoded document to Cloudinary and get back the file URL.

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body (JSON):
  ```json
  {
    "file_base64": "base64_encoded_file_content",
    "filename": "document.pdf",
    "folder": "tuition_master/documents",
    "resource_type": "auto",
    "public_id": null,
    "overwrite": false
  }
  ```
  - `file_base64` (required): Base64 encoded file content (with or without data URI prefix)
  - `filename` (required): Original filename with extension (e.g., "document.pdf")
  - `folder` (optional): Cloudinary folder path (default: "tuition_master/documents")
  - `resource_type` (optional): Resource type - "auto", "image", "raw", "video" (default: "auto")
  - `public_id` (optional): Custom public ID for the file
  - `overwrite` (optional): Whether to overwrite existing files (default: false)

**Response:**
```json
{
  "success": true,
  "url": "https://res.cloudinary.com/your_cloud/image/upload/v1234567890/tuition_master/documents/filename.pdf",
  "public_id": "tuition_master/documents/filename",
  "format": "pdf",
  "resource_type": "raw",
  "bytes": 123456,
  "width": null,
  "height": null,
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "file_base64": "JVBERi0xLjQKJeLjz9MKMy...",
    "filename": "document.pdf",
    "folder": "tuition_master/documents",
    "resource_type": "auto"
  }'
```

**Example using Python requests:**
```python
import requests
import base64

# Read file and encode to base64
with open("document.pdf", "rb") as f:
    file_bytes = f.read()
    file_base64 = base64.b64encode(file_bytes).decode('utf-8')

url = "http://localhost:8000/api/documents/upload"
payload = {
    "file_base64": file_base64,
    "filename": "document.pdf",
    "folder": "tuition_master/documents",
    "resource_type": "auto"
}

response = requests.post(url, json=payload)
print(response.json())
```

**Example with data URI prefix (also supported):**
```python
import requests
import base64

# Read file and encode to base64 with data URI prefix
with open("document.pdf", "rb") as f:
    file_bytes = f.read()
    file_base64 = f"data:application/pdf;base64,{base64.b64encode(file_bytes).decode('utf-8')}"

url = "http://localhost:8000/api/documents/upload"
payload = {
    "file_base64": file_base64,
    "filename": "document.pdf",
    "folder": "tuition_master/documents"
}

response = requests.post(url, json=payload)
print(response.json())
```

### 2. Upload Document (Multipart Form Data) - Alternative

**Endpoint:** `POST /api/documents/upload-multipart`

**Description:** Upload a document file via multipart form data to Cloudinary (alternative to base64 upload).

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file` (required): The file to upload
  - `folder` (optional): Cloudinary folder path (default: "tuition_master/documents")
  - `resource_type` (optional): Resource type - "auto", "image", "raw", "video" (default: "auto")
  - `public_id` (optional): Custom public ID for the file
  - `overwrite` (optional): Whether to overwrite existing files (default: false)

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload-multipart" \
  -F "file=@/path/to/your/document.pdf" \
  -F "folder=tuition_master/documents" \
  -F "resource_type=auto"
```

**Example using Python requests:**
```python
import requests

url = "http://localhost:8000/api/documents/upload-multipart"
files = {"file": open("document.pdf", "rb")}
data = {
    "folder": "tuition_master/documents",
    "resource_type": "auto"
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### 3. Upload Document from Server Path

**Endpoint:** `POST /api/documents/upload-from-path`

**Description:** Upload a document from a local file path on the server to Cloudinary.

**Request:**
- Method: `POST`
- Content-Type: `application/x-www-form-urlencoded`
- Body:
  - `file_path` (required): Local file path on the server
  - `folder` (optional): Cloudinary folder path
  - `resource_type` (optional): Resource type
  - `public_id` (optional): Custom public ID
  - `overwrite` (optional): Whether to overwrite

**Example:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload-from-path" \
  -d "file_path=/path/to/document.pdf" \
  -d "folder=tuition_master/documents"
```

### 4. Get Document URL

**Endpoint:** `GET /api/documents/url/{public_id}`

**Description:** Get the URL for a document stored in Cloudinary using its public_id.

**Request:**
- Method: `GET`
- Path Parameter: `public_id` - The public ID of the file (include folder path if applicable)
- Query Parameter: `resource_type` (optional) - Resource type (default: "auto")

**Response:**
```json
{
  "url": "https://res.cloudinary.com/your_cloud/image/upload/v1234567890/tuition_master/documents/filename.pdf",
  "public_id": "tuition_master/documents/filename"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/documents/url/tuition_master/documents/filename?resource_type=auto"
```

### 5. Delete Document

**Endpoint:** `DELETE /api/documents/delete/{public_id}`

**Description:** Delete a document from Cloudinary using its public_id.

**Request:**
- Method: `DELETE`
- Path Parameter: `public_id` - The public ID of the file to delete (include folder path if applicable)
- Query Parameter: `resource_type` (optional) - Resource type (default: "auto")

**Response:**
```json
{
  "success": true,
  "result": "ok"
}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/documents/delete/tuition_master/documents/filename?resource_type=auto"
```

## Usage Examples

### Upload a PDF Document (Base64)

```python
import requests
import base64

# Read and encode PDF to base64
with open("class_notes.pdf", "rb") as f:
    file_bytes = f.read()
    file_base64 = base64.b64encode(file_bytes).decode('utf-8')

# Upload to Cloudinary
url = "http://localhost:8000/api/documents/upload"
payload = {
    "file_base64": file_base64,
    "filename": "class_notes.pdf",
    "folder": "tuition_master/class_notes",
    "resource_type": "raw"
}

response = requests.post(url, json=payload)
result = response.json()

if result["success"]:
    print(f"File uploaded successfully!")
    print(f"URL: {result['url']}")
    print(f"Public ID: {result['public_id']}")
```

### Upload an Image (Base64)

```python
import requests
import base64

# Read and encode image to base64
with open("student_photo.jpg", "rb") as f:
    file_bytes = f.read()
    file_base64 = base64.b64encode(file_bytes).decode('utf-8')

# Upload to Cloudinary
url = "http://localhost:8000/api/documents/upload"
payload = {
    "file_base64": file_base64,
    "filename": "student_photo.jpg",
    "folder": "tuition_master/student_photos",
    "resource_type": "image"
}

response = requests.post(url, json=payload)
result = response.json()
print(f"Image URL: {result['url']}")
```

### Upload from Frontend (JavaScript)

```javascript
// Convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

// Upload document
async function uploadDocument(file) {
    const fileBase64 = await fileToBase64(file);
    
    const response = await fetch('http://localhost:8000/api/documents/upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            file_base64: fileBase64,
            filename: file.name,
            folder: 'tuition_master/documents',
            resource_type: 'auto'
        })
    });
    
    const result = await response.json();
    if (result.success) {
        console.log('Uploaded URL:', result.url);
        return result.url;
    }
}
```

### Store URL in Database

After uploading, you can store the returned URL in your database:

```python
# After successful upload
document_url = result["url"]
public_id = result["public_id"]

# Store in your database model
# Example: Update a student record with document URL
```

## Notes

- Files are automatically uploaded to the `tuition_master/documents` folder by default
- The `resource_type="auto"` will automatically detect the file type
- All URLs returned are HTTPS secure URLs
- The public_id includes the folder path, so use the full path when deleting or getting URLs
- Cloudinary free tier includes 25 GB storage and 25 GB monthly bandwidth

## Testing

You can test the endpoints using:
1. FastAPI interactive docs at `http://localhost:8000/docs`
2. cURL commands (examples above)
3. Python requests library (examples above)
4. Postman or any HTTP client

## Troubleshooting

1. **Import errors**: Make sure you've installed the requirements: `pip install -r requirements.txt`
2. **Authentication errors**: Verify your Cloudinary credentials in the `.env` file
3. **Upload failures**: Check file size limits (Cloudinary free tier: 10 MB per file)
4. **URL not working**: Ensure the public_id includes the full folder path

