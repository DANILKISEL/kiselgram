#!/bin/bash

echo "📱 Starting Kiselgram Mobile..."
echo "🌐 Server will be available at: http://localhost:5000"
echo "📱 Open on mobile: Use your local IP address"
echo ""

# Get local IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')
echo "📡 Access from other devices: http://$IP_ADDRESS:5000"
echo ""

# Start the application
python3 kiselgram_app.py
