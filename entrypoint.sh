#!/bin/sh
set -e

# The /tap/certificates/certificate.pfx file is only present on TAP and is auto-placed in the
# container as long as the "Enable Automatic Certificate Generation" setting is set to true.
# Extract the private key from pfx file, this is for supporting the SSL-based Kafka authentication.
openssl pkcs12 -in /tap/certificates/certificate.pfx -nocerts -out /tap/certificates/key.pem -nodes -passin pass:""
# Extract the certificate from pfx file, this is for supporting the SSL-based Kafka authentication.
openssl pkcs12 -in /tap/certificates/certificate.pfx -nokeys -out /tap/certificates/cert.pem -passin pass:""

# Start Supervisor to manage both (Celery worker in the foreground and Gunicorn application server) processes
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
