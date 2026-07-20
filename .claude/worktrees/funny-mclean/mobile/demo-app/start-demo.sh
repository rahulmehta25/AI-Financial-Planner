#!/bin/bash

# Financial Planner Demo - Quick Start Script
echo "🚀 Financial Planner Demo - Starting..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "Visit: https://nodejs.org"
    exit 1
fi

# Check if Expo CLI is installed
if ! command -v expo &> /dev/null; then
    echo "📱 Installing Expo CLI..."
    npm install -g expo-cli
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "✅ Setup complete!"
echo ""
echo "🎯 Demo Features:"
echo "  • Beautiful onboarding flow"
echo "  • Biometric authentication (demo@financialplanner.com / demo123)"
echo "  • Portfolio dashboard with charts"
echo "  • Goal tracking with animations"
echo "  • Push notifications"
echo "  • Dark/light theme toggle"
echo "  • Offline functionality"
echo ""
echo "📱 To test on your phone:"
echo "  1. Install 'Expo Go' from App Store/Google Play"
echo "  2. Scan the QR code that appears"
echo ""
echo "🚀 Starting Expo development server..."
echo ""

# Start Expo
expo start