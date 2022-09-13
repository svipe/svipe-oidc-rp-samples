# Svipe OIDC (OpenID Connect) samples for RPs (Relying Parties)

This repo contains sample apps in python that demonstrate two ways of using
Svipe iD to create a login flow:

1. Auth Flow that uses the QR Code page created by Svipe
2. Auth Flow with client-side pre-loaded QR Code parameters


## Auth Flow that uses the QR Code page created by Svipe

This is the easiest way to integrate with Svipe iD and requires minimal coding
in the RP. However, there is less control over the look & feel as the QR-code
page is created by Svipe.

## Auth Flow with client-side pre-loaded QR Code parameters

This example uses a special feature where (most) of the authorization parameters
are pre-defined in the OIDC admin interface and the QR-code only contains the
`client-id`, the `state`, and the `nonce`. This means that the qr-code can be
created entirely by the RP and kept fairly small.

However, since the QR-code is scanned by the user with the Svipe iD-app, the
page needs to communicate with the svipe oidc-backed so that it gets notified
when the user has scanned the code and approved the sharing of information. This
is done using a socketio connection to api.svipe.com.
`2_Auth_Flow_Preloaded_Qrcode/templates/logged_out.html` contains the details
for how this is done.


## Server variants

For each example there are 3 python server implementations:
* **authlib-fastapi** uses the authlib oidc library for the oidc interaction and the fastapi framework for the app
* **authlib-flask** also uses the authlib oidc library but in combination with the flask framework
* **nolib-fastapi** implements the oidc interaction directly and uses the fastapi framework for the app.

## Launching a server

The servers can either be launched directly:

    1_Auth_Flow/app-authlib-fastapi.py

Or by using gunicorn:

    gunicorn --chdir 1_Auth_Flow -b 0.0.0.0:9000 app-authlib-flask:app

Note that fastapi requires the uvicorn worker class to be specified:

    gunicorn --chdir 1_Auth_Flow -b 0.0.0.0:9000 app-authlib-fastapi:app --worker-class uvicorn.workers.UvicornWorker

## Specifying a configuration

The configuration file `config.yaml` contains several oidc sample
configurations. The default config that uses the sample svipe-demo credentials
is:

    default:
      issuer:         'https://api.svipe.com/oidc/v1'
      client_id:      'svipe-demo'
      client_secret:  'svipe-demo-secret'
      scope:          'openid profile'
      pkce:           True

Provide the name of the config as a command-line argument to use it:

    1_Auth_Flow/app-authlib-fastapi.py email

Uses the email config:

    email:
      issuer:         'https://api.svipe.com/oidc/v1'
      client_id:      'svipe-demo'
      client_secret:  'svipe-demo-secret'
      scope:          'openid profile email'
      pkce:           True

Which means that Svipe iD will require the email to be specified in order to
login.


1. pre-loaded QR-code parameters for the QR code so that it can be created client side and integre

Auth Flow - An Express + Passport app example
Implicit Flow - A Single Page App (SPA) example
Password Grant - A sample using the Resource Owner Password Grant
Auth Flow + PKCE - Best practice for SPA or native mobile apps


## Svipe iD sample app

This is a sample app for how to use Svipe iD to authenticate a user with a
python backend app built using Flask. This is the easiest way to integrate with
Svipe iD and requires minimal coding. It does however bring up an authentication
page from Svipe with a QR code (for the laptop use case) or an authentication
button (when used directly on a mobile).

## Launch

You can either launch the app directly with python:

    python app.py

or use a WSGI-compliant server that also supports reloading when the site
changes (in case you want to experiment):

    gunicorn -b 0.0.0.0:9000 --reload app:app

## Configuration

The configuration file `config.yaml` contains two configurations:

* default - the standard configuration using PKCE
* nopkce - use client_secret instead of pkce

Using PKCE is strongly recommended and you can read more about it
(here)[https://dropbox.tech/developers/pkce--what-and-why-]



    python app-flask.py
    python app-fastapi.py

or use a WSGI-compliant server that also supports reloading when the site
changes:

    gunicorn -b 0.0.0.0:9000 --reload app-flask:app


    uvicorn --host 0.0.0.0 --port 9000 --reload app-fastapi:app

## Using your own OIDC-credentials

The samples in the config file use the svipe-demo credentials. However, to
define your custom OIDC redirect urls, pre-loaded parameters, head over to the
Svipe Developer Portal at [developer.svipe.com](https://developer.svipe.com),
login using your Svipe iD, and define your custom apps on
[developer.svipe.com/applications](https://developer.svipe.com/applications).

The developer portal also has a [documentation
section](https://developer.svipe.com/documentation) that contains more
information about the OIDC parameters as well as examples for other frameworks
(Node.js / Django and Ruby) as well as examples on how to use Svipe iD for some
common applications (WordPress / Keycloak / Matrix / Mattermost / Nextcloud).
