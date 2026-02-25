#!/bin/bash
# Run as root or with sudo on the host:
#   sudo bash /home/quant/apps/quantclaw-data/setup-nginx.sh

cat > /etc/nginx/sites-available/data.moneyclaw.com << 'EOF'
server {
    listen 80;
    server_name data.moneyclaw.com;
    location / {
        proxy_pass http://127.0.0.1:3055;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
ln -sf /etc/nginx/sites-available/data.moneyclaw.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
echo "Done: data.moneyclaw.com -> port 3055"
