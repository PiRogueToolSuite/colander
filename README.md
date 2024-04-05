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
Check the [deployment procedure on our website](https://pts-project.org/docs/colander/deployment/).

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

