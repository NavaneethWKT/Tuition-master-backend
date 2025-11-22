#!/bin/bash
# Start ngrok tunnel for FastAPI server on port 8000

echo "Starting ngrok tunnel on port 8000..."
echo "Note: If this is your first time, you may need to sign up at https://dashboard.ngrok.com/signup"
echo "Then run: ngrok config add-authtoken YOUR_AUTH_TOKEN"
echo ""
echo "Ngrok web interface will be available at: http://localhost:4040"
echo ""

# Start ngrok with browser warning disabled
ngrok http 8000 --request-header-add "ngrok-skip-browser-warning: true"

