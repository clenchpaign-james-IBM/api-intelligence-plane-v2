#!/bin/bash
# Zero-Trust TLS Setup for API Intelligence Plane
# Implements mTLS between all components

set -e

echo "=== Zero-Trust TLS Setup ==="
echo ""

# Create certificates directory
mkdir -p certs/{ca,opensearch,backend,frontend,mcp,gateway}

# Generate CA if it doesn't exist
if [ ! -f "certs/ca/ca-key.pem" ]; then
    echo "Generating Certificate Authority..."
    openssl genrsa -out certs/ca/ca-key.pem 4096
    openssl req -new -x509 -days 3650 -key certs/ca/ca-key.pem -out certs/ca/ca-cert.pem \
        -subj "/C=US/ST=State/L=City/O=AIP/CN=AIP-CA"
    echo "✓ CA generated"
fi

# Function to generate certificate
generate_cert() {
    local name=$1
    local cn=$2
    local dir=$3
    
    echo "Generating certificate for $name..."
    
    # Generate private key
    openssl genrsa -out "$dir/${name}-key.pem" 4096
    
    # Generate CSR
    openssl req -new -key "$dir/${name}-key.pem" -out "$dir/${name}-csr.pem" \
        -subj "/C=US/ST=State/L=City/O=AIP/CN=$cn"
    
    # Create extensions file
    cat > "$dir/${name}-ext.cnf" <<EOF
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $cn
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF
    
    # Sign certificate
    openssl x509 -req -in "$dir/${name}-csr.pem" \
        -CA certs/ca/ca-cert.pem -CAkey certs/ca/ca-key.pem -CAcreateserial \
        -out "$dir/${name}-cert.pem" -days 365 \
        -extfile "$dir/${name}-ext.cnf"
    
    # Create full chain
    cat "$dir/${name}-cert.pem" certs/ca/ca-cert.pem > "$dir/${name}-fullchain.pem"
    
    # Copy CA cert
    cp certs/ca/ca-cert.pem "$dir/"
    
    # Set permissions
    chmod 600 "$dir/${name}-key.pem"
    chmod 644 "$dir/${name}-cert.pem"
    
    echo "✓ Certificate for $name generated"
}

# Generate certificates for all components
generate_cert "opensearch" "opensearch" "certs/opensearch"
generate_cert "backend" "backend" "certs/backend"
generate_cert "frontend" "frontend" "certs/frontend"
generate_cert "mcp-unified" "mcp-unified" "certs/mcp"
generate_cert "mcp-unified" "mcp-unified" "certs/mcp"
generate_cert "mcp-unified" "mcp-unified" "certs/mcp"
generate_cert "gateway" "demo-gateway" "certs/gateway"

echo ""
echo "=== TLS Setup Complete ==="
echo "All certificates generated in ./certs/"
echo ""

# Made with Bob
