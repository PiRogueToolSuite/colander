log:
  level: INFO

entryPoints:
  web:
    # http
    address: ":80"
    http:
      # https://docs.traefik.io/routing/entrypoints/#entrypoint
      redirections:
        entryPoint:
          to: web-secure

  web-secure:
    # https
    address: ":443"

certificatesResolvers:
  letsencrypt:
    # https://docs.traefik.io/master/https/acme/#lets-encrypt
    acme:
      email: "${ACME_EMAIL}"
      storage: /etc/traefik/acme/acme.json
      # https://docs.traefik.io/master/https/acme/#httpchallenge
      httpChallenge:
        entryPoint: web

http:
  routers:
    web-secure-django:
      rule: "Host(\"${COLANDER_FQDN}\")"
      entryPoints:
        - web-secure
      middlewares:
        - compress-http
        - csrf
      service: django
      tls:
        certResolver: letsencrypt
    web-secure-threatr:
      rule: "Host(\"${THREATR_FQDN}\")"
      entryPoints:
        - web-secure
      middlewares:
        - compress-http
        - csrf
      service: threatr
      tls:
        certResolver: letsencrypt
    web-secure-cyberchef:
      rule: "Host(\"${CYBERCHEF_FQDN}\")"
      entryPoints:
        - web-secure
      middlewares:
        - compress-http
        - csrf
      service: cyberchef
      tls:
        certResolver: letsencrypt
    web-secure-keycloak:
      rule: "Host(\"${KEYCLOAK_FQDN}\")"
      entryPoints:
        - web-secure
      middlewares:
        - compress-http
        - csrf
      service: keycloak
      tls:
        certResolver: letsencrypt

  middlewares:
  	compress-http:
  	  # https://doc.traefik.io/traefik/middlewares/http/compress/
	  compress: true
    csrf:
      # https://docs.traefik.io/master/middlewares/headers/#hostsproxyheaders
      # https://docs.djangoproject.com/en/dev/ref/csrf/#ajax
      headers:
        hostsProxyHeaders: ["X-CSRFToken"]

  services:
    colander:
      loadBalancer:
        servers:
          - url: http://colander-front:5000
    threatr:
      loadBalancer:
        servers:
          - url: http://threatr-front:5000
    cyberchef:
      loadBalancer:
        servers:
          - url: http://cyberchef:8000
    keycloak:
      loadBalancer:
        servers:
          - url: http://keycloak:8000

providers:
  # https://docs.traefik.io/master/providers/file/
  file:
    filename: /etc/traefik/traefik.yml
    watch: true
