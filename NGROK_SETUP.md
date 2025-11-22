# Ngrok Setup Guide

## Bypassing the Browser Warning Page

When using ngrok's free plan, you may encounter an HTML warning page instead of your API responses. To bypass this, add the following header to all your API requests:

### Header Details:
- **Header Name:** `ngrok-skip-browser-warning`
- **Header Value:** Any value (e.g., `true`, `1`, or any string)

### Example Usage:

#### JavaScript/Fetch:
```javascript
fetch('https://your-ngrok-url.ngrok-free.app/api/health', {
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
})
```

#### Axios:
```javascript
axios.get('https://your-ngrok-url.ngrok-free.app/api/health', {
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
})
```

#### cURL:
```bash
curl -H "ngrok-skip-browser-warning: true" \
  https://your-ngrok-url.ngrok-free.app/api/health
```

#### Postman/Insomnia:
Add a custom header:
- Key: `ngrok-skip-browser-warning`
- Value: `true`

## Starting Ngrok

Use the provided script:
```bash
./start_ngrok.sh
```

Or manually:
```bash
ngrok http 8000 --request-header-add "ngrok-skip-browser-warning: true"
```

## Important Notes

1. This header must be sent **from the client** making the request to ngrok
2. The FastAPI server is configured to accept this header via CORS
3. The header can have any value - ngrok just checks for its presence
4. This only works with the free plan - paid plans don't show the warning page

