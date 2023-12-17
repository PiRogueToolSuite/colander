<div align="center">
<img width="60px" src="https://pts-project.org/android-chrome-512x512.png">
<h1>Colander</h1>
<p>
Colander is an incident response and knowledge management platform, delivered as a cloud-agnostic software stack, that organizations can deploy. It takes events, artifacts, observables extracted from artifacts or from 3rd-party providers, and turns them into browsable knowledge. Organized in cases, knowledge is then processed to automatically generate reports, detection rules and intelligence feeds.
</p>
<p>
License: GPLv3
</p>
</div>

# Features

* Organize knowledge in different cases
* Invite team member to collaborate to your cases
* Represent the real world with generic entities such as artifact, actor, observable, event and more
* Graph knowledge using the dynamic graph editor
* Write documentation at anytime
* Import intelligence from 3rd-party service such as VirusTotal or OTX Alien Vault
* Collect and sign artifacts directly from your PiRogue
* Analyze decrypted network traffic and payloads
* Decode network payload with CyberChef
* Apply Yara rules directly on the network traffic
* Ensure artifact integrity and authenticity
* Create feeds to export your findings in different formats

# Architecture
Colander relies on different services:

* `colander-postgres`: Postgres database
* `colander-front`: Gunicorn serving the pages of Colander 
* `colander-worker`: Django Q2 cluster of workers
* `traefik`: Traefik reverse proxy ensuring TLS termination and routing
* `cyberchef`: CyberChef instance  
* `playwright`: service using Playwright to take URL screenshot and capture the HAR
* `elasticsearch`: single node ElasticSearch server storing network traffic analysis
* `minio`: Minio S3-compatible object storage to store artifacts
* `redis`: Redis server ensuring the communication between the front and the workers for both Colander and Threatr
* `watchtower`: Watchtower service keeping the stack up to date

Colander comes with Threatr which relies on:

* `threatr-postgres`: Postgres database
* `threatr-front`: Gunicorn serving the pages of Threatr 
* `threatr-worker`: Django Q2 cluster of workers

# Production environment
Colander official Docker image is available [on GitHub](https://github.com/PiRogueToolSuite/colander/pkgs/container/colander). The stack we provide comes with the service [Watchtower](https://containrrr.dev/watchtower/) that will automatically update the version of Colander you deployed.

## Requirements
We suggest to use a dedicated server with at least:

* 4 cores
* 4GB of RAM
* 500GB of storage space

We recommend to install Debian as is the operating system we know, and we will be able to guide you through all different steps for installation, maintenance and debugging. 

Your server must have a public IP address as well as a domain name.

## Deployment procedure
Once your server is up and running, download the Colander deployment package available on GitHub and decompress it on your server. 

### Configuration
The next step is to configure the stack to be deployed. To do so, edit the file `.envs/.tpl/.base` and set the following variables according to your production environment:

* `ACME_EMAIL`: the email address attached to the TLS certificate
* `ADMIN_NAME`: full name of the administrator
* `ADMIN_EMAIL`: email address that will receive notifications on crashes and unhandled errors
* `ROOT_DOMAIN`: the domain name pointing to your server 
* `DJANGO_DEFAULT_FROM_EMAIL`: the email address used for sending emails
* `EMAIL_HOST`: the host to use for sending email (can be the SMTP server of your email provider)
* `EMAIL_HOST_USER`: the username to use for the SMTP server
* `EMAIL_HOST_PASSWORD`: the password to use for the SMTP server 
* `EMAIL_PORT`: the port to use for the SMTP server 
* `EMAIL_USE_TLS`: `True` if the SMTP server uses TLS, `False` otherwise
* `EMAIL_USE_SSL`: `True` if the SMTP server uses SSL, `False` otherwise

Find more details about the email configuration in the [Django documentation](https://docs.djangoproject.com/en/4.2/ref/settings/#email-use-tls).

Once configured, you have to generate the entire configuration of the stack by running the following command:

```
bash gen.sh
```

The script will generate multiple files containing environment variables that will be passed to the different services.

### First boot
Now, you are ready to fire up the stack using `docker compose`:

```
docker compose -f no-sso.yml build
docker compose -f no-sso.yml up -d 
```

The Colander stack is now starting, you can see the logs by running 

```
docker compose -f no-sso.yml logs
```

Check with your web browser if Colander is up by browsing the domain name you configured.

### Admin user
Next, you have to create an admin user for both Colander and Threatr by running 

```
docker compose -f no-sso.yml run --rm colander-front python manage.py createsuperuser
docker compose -f no-sso.yml run --rm threatr-front python manage.py createsuperuser
```

and follow the instructions.

**Don't forget to save the credentials in your favorite password manager!**

Note that the administration panels are accessible at random URLs specified in the files `.envs/.production/.colander` and `.envs/.production/.threatr`.

### Insert default data
Colander and Threatr come with a set of predefined entity types, to load them, run the following command

```
docker compose -f no-sso.yml run --rm colander-front python manage.py insert_default_data
docker compose -f no-sso.yml run --rm threatr-front python manage.py insert_default_data
```

### Connect Colander to Threatr
In the administration panel of Threatr, create a regular user via the *Users* menu. Then, via the *Auth Token* menu, create a new API key for the user you just created. Next, via the menu *Vendor credentials*, create a new entry for each 3rd-party API key you have for Virus Total and/or OTX Alien Vault.

* for VirusTotal, use the vendor identified `vt` and for the credentials field, set 
    ```json
      {"api_key": "your VT API key"}
    ```
* for OTX Alien Vault, use the vendor identified `otx` and for the credentials field, set 
    ```json
      {"api_key": "your OTX API key"}
    ```

In the administration panel of Colander, via the menu *Backend credentials*, create a new entry with `threatr` as backend identifier and for the credentials field, set 
    ```json
      {"api_key": "your Threatr API key"}
    ```

# Development environment

## Setup
The development environment relies on Docker Compose (or Podman). The file `local.yml` provides the entire stack you need.

```
git clone https://github.com/PiRogueToolSuite/colander.git
cd colander
docker compose -f local.yml build 
docker compose -f local.yml up -d
docker compose -f local.yml run --rm django python manage.py insert_default_data
docker compose -f local.yml run --rm django python manage.py createsuperuser 
docker compose -f local.yml logs -f -n 44 django
```
Then, you should be able to browse and log-in Colander at [http://localhost:8000](http://localhost:8000).

To stop your Colander stack:
```
docker compose -f local.yml stop
```

## Basic Commands

### Setting up users

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

* To create a **superuser account**, use this command:
```
python manage.py createsuperuser
```

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

By default, registration is disabled on Colander. To create new regular users, you have to do it using the administration panel at http://localhost:8000/admin/  

### Building Docker images
The frontend service named `django` will automatically reload when files are modified. But, the `worker` service will not. So, if you modify or add an asynchronous task that will be executed by a worker, you have to restart the corresponding service. 

```
docker compose -f local.yml restart worker
```

If you modify the dependencies in the folder `requirements`, you have to rebuild the `django` image.

```
docker compose -f local.yml build django
```

### Updating the default data
Colander comes with a set of predefined entity types listed in `colander/core/management/commands/data/`. To apply changes, run the following command

```
docker compose -f local.yml run --rm django python manage.py insert_default_data
```

### Type checks

Running type checks with mypy:
```
mypy colander
```

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:
```
coverage run -m pytest
coverage html
open htmlcov/index.html
```

#### Running tests with pytest
```
pytest
```

