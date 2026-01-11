# RSS Feed Aggregator

RSS Feed Aggregator is Python script __*feed.py*__

It reads feeds from various RSS sources and generates aggregated Web Page (./html/index.html) and RSS Feeed (./html/combined.xml)

Solution configuration used in this repository is used to provide aggregator of all my blogs. It is available at HTTPS://blog.uw.cz

However, the solution can be easily customized for any RSS sources. Customization variables __RSS Sources__ and __Title__ are defined at the beginning of python script.

```code
# RSS Sources
sources = [
    "https://vcdx200.uw.cz/feeds/posts/default",
    "https://linux.uw.cz/feeds/posts/default",
    "https://freebsd.uw.cz/feeds/posts/default",
    "https://itkb.uw.cz/feeds/posts/default",
    "https://philosophy.uw.cz/feeds/posts/default",
    "https://itc-bohemians.blogspot.com//feeds/posts/default"
]

# Title to be used in generated files
TITLE="Aggregated RSS feed from all uw.cz blogs"

# BLOG URL to be used in RSS Feed (OUTPUT_RSS_FILE) and Web Page File (OUTPUT_HTML_FILE)
BLOG_URL = "https://blog.uw.cz/"
```
# Dockerized Deployment

## RSS-GENERATOR

Python script runs as container __rss-generator__ and generates files (index.html, rss.xml) into __./html__ directory.

```code
  rss-generator:
    image: python:3.12-slim 
    container_name: rss-generator
    volumes:
      - ./html:/usr/share/nginx/html
      - ./feed.py:/app/feed.py 
    working_dir: /app
    command: | 
      sh -c '
      pip install --no-cache-dir feedparser feedgen
      while true; do
        python feed.py
        sleep 60
      done
      '
```

## NGINX

NGINX is the Web Server providing generated static files (index.html, rss.xml) in __./html__ directory via HTTP protocol. 

NGINX runs locally on port :8080 and serves as a backend web server behind HAProxy which provides TLS/SSL Termination.

```code
  rss-nginx:
    image: nginx:latest
    container_name: rss-nginx
    ports:
      - "8080:80"
    networks: 
      - web
    volumes:
      - ./html:/usr/share/nginx/html:ro
    restart: unless-stopped
```

## HAProxy

HAProxy is the Load Balancer providing TLS/SSL Termination and serving NGINX Web Server content.

```code
  haproxy:
    image: haproxy:latest
    container_name: haproxy
    user: root
    networks:
      - web
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./certs:/usr/local/etc/haproxy/certs:ro
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    restart: unless-stopped
```

## ACME

ACME is the solution to automatically generate and renew TLS/SSL certificates. 

In this particular solution we use ZeroSSL (https://zerossl.com/), but Let's Encrypt (https://letsencrypt.org/) can be used as well and is fully suported by ACME.

```code
  acme:
    image: neilpang/acme.sh
    container_name: acme
    networks:
      - web
    volumes:
      - ./certs:/acme.sh
    environment:
      - Active24_ApiKey=${Active24_ApiKey}
      - Active24_ApiSecret=${Active24_ApiSecret}
      - ZERO_SSL_EAB_EMAIL=david.pasek@gmail.com   # REQUIRED for ZeroSSL
    command: |
      sh -c '
      # Set ZeroSSL as default CA
      acme.sh --set-default-ca --server zerossl

      # Register account (safe to run multiple times)
      acme.sh --register-account -m david.pasek@gmail.com

      # Issue certificate only if it does not exist
      if [ ! -f /acme.sh/blog.uw.cz_ecc/fullchain.cer ]; then
        acme.sh --issue --dns dns_active24 -d blog.uw.cz
      fi

      # Install certificate (idempotent)
      acme.sh --install-cert -d blog.uw.cz --ecc \
        --fullchain-file /acme.sh/blog.uw.cz_ecc/fullchain.cer \
        --key-file /acme.sh/blog.uw.cz_ecc/blog.uw.cz.key \
        --reloadcmd "kill -HUP 1"

      # Create PEM certificate
      cat /acme.sh/blog.uw.cz_ecc/blog.uw.cz.key /acme.sh/blog.uw.cz_ecc/fullchain.cer > /acme.sh/blog.uw.cz_ecc/blog.uw.cz.pem
      chmod 600 /acme.sh/blog.uw.cz_ecc/blog.uw.cz.pem

      # Run ACME Cron and Wait 24 hours for next run
      while true; do
        acme.sh --cron
        sleep 86400 # Sleep 24 hours
      done
      '
    restart: unless-stopped
```
