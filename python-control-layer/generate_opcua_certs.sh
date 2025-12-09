#!/bin/bash
#
# Generate self-signed certificates for MODAX OPC UA Server
#
# Usage: ./generate_opcua_certs.sh [cert_dir]
#
# Default cert_dir: ./certs
#

set -e

CERT_DIR="${1:-certs}"

# Create certificate directory if it doesn't exist
mkdir -p "$CERT_DIR"

echo "Generating OPC UA certificates in $CERT_DIR..."

# Generate server certificate
echo "Generating server certificate..."
openssl req -x509 -newkey rsa:2048 \
    -keyout "$CERT_DIR/server_key.pem" \
    -out "$CERT_DIR/server_cert.pem" \
    -days 365 -nodes \
    -subj "/C=DE/ST=State/L=City/O=MODAX/CN=modax-server"

# Convert to DER format (required by asyncua)
openssl x509 -in "$CERT_DIR/server_cert.pem" -outform der -out "$CERT_DIR/server_cert.der"

# Generate client certificate (optional, for secure client connections)
echo "Generating client certificate..."
openssl req -x509 -newkey rsa:2048 \
    -keyout "$CERT_DIR/client_key.pem" \
    -out "$CERT_DIR/client_cert.pem" \
    -days 365 -nodes \
    -subj "/C=DE/ST=State/L=City/O=MODAX/CN=modax-client"

# Convert to DER format
openssl x509 -in "$CERT_DIR/client_cert.pem" -outform der -out "$CERT_DIR/client_cert.der"

# Set appropriate permissions
chmod 600 "$CERT_DIR"/*.pem
chmod 644 "$CERT_DIR"/*.der

echo "✓ Certificates generated successfully!"
echo ""
echo "Server certificates:"
echo "  - $CERT_DIR/server_cert.der"
echo "  - $CERT_DIR/server_key.pem"
echo ""
echo "Client certificates:"
echo "  - $CERT_DIR/client_cert.der"
echo "  - $CERT_DIR/client_key.pem"
echo ""
echo "To enable OPC UA security, set these environment variables:"
echo "  export OPCUA_ENABLE_SECURITY=true"
echo "  export OPCUA_CERT_DIR=$CERT_DIR"
