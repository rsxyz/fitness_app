# fitness_app
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install wheel flask gunicorn
pip freeze > requirements.txt
```
```sh
FLASK_APP=app.py FLASK_ENV=development flask run --host=0.0.0.0 --port=5000
```

## from project root, virtualenv active
```sh

gunicorn -w 4 -b 127.0.0.1:5001 app:app
Test: open http://127.0.0.1:5001
```

## create a minimal Nginx reverse proxy (HTTP)
```sh
brew install nginx
mkdir -p /usr/local/etc/nginx/servers/
sudo mkdir -p /usr/local/var/run/nginx
sudo mkdir -p /usr/local/var/log/nginx
sudo mkdir -p /usr/local/var/tmp/nginx/{client_body,proxy,fastcgi,uwsgi,scgi}
sudo chown -R $(whoami) /usr/local/var

cp fitness_app_nginx.conf /usr/local/etc/nginx/servers/
nginx -t
brew services restart nginx


```

## make Flask trust proxy headers

```sh
When behind Nginx, Flask needs ProxyFix to correctly detect scheme and IP:
from werkzeug.middleware.proxy_fix import ProxyFix

# tell Flask how many proxies to trust (set to 1 for single nginx)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
```