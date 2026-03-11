#!/bin/bash
# Restart services to apply configuration changes

echo "🔄 Stopping containers..."
docker-compose down

echo "🏗️  Rebuilding frontend container..."
docker-compose build frontend

echo "🚀 Starting all services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "✅ Services restarted!"
echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "🌐 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Query Page: http://localhost:3000/query"
echo ""
echo "📝 To view logs:"
echo "   docker-compose logs -f frontend"
echo "   docker-compose logs -f backend"

# Made with Bob
