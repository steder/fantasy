#!/usr/bin/env bash

set -e -u -x

# Generate a private key
openssl genrsa -des3 -out server.key 1024

# Generate a CSR
openssl req -new -key server.key -out server.csr

# Remove Passphrase from key
cp server.key server.key.org
openssl rsa -in server.key.org -out server.key

# Generate self signed certificate
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
