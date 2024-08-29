#!/bin/bash

SSL_DIR="/etc/ssl"
CERT_FILE="$SSL_DIR/certs/cert.pem"
KEY_FILE="$SSL_DIR/private/key.pem"

mkdir -p $SSL_DIR/certs
mkdir -p $SSL_DIR/private

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $KEY_FILE -out $CERT_FILE -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=localhost"

nginx -g 'daemon off;'

