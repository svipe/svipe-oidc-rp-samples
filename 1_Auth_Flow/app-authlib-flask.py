#!/usr/bin/env python3
 
# Copyright (c) 2022 Svipe AB (https://www.svipe.com)
# Author: Stefan Farestam <stefan@svipe.com>
# You may use, distribute and modify this code under the terms of the MIT License

import requests
import yaml
import os
import sys
import pathlib
import secrets

import flask
from   authlib.integrations.flask_client import OAuth

os.chdir(pathlib.Path(__file__).parent)

config_file = pathlib.Path('../config.yaml')
config_info = yaml.safe_load(config_file.read_text())
if not (config_name := sys.argv[-1]) in config_info:
    config_name = 'default'
config = config_info.get(config_name)

app = flask.Flask(__name__,
    template_folder = 'templates',
    static_folder   = 'static',
)
session_secret = secrets.token_urlsafe(32)
app.secret_key = session_secret

client_kwargs = {'scope': config.get('scope')}
if config.get('pkce') == True:
    client_kwargs['code_challenge_method'] = 'S256'

oauth = OAuth(app=app)
oauth.register(
    name                = 'svipe',
    client_id           = config.get('client_id'),
    client_secret       = config.get('client_secret'),
    server_metadata_url = f"{config.get('issuer')}/.well-known/openid-configuration",
    client_kwargs       = client_kwargs,
)


@app.route('/')
def index():
    if userinfo := flask.session.get('userinfo'):
        return flask.render_template('logged_in.html', userinfo=userinfo)
    else:
        return flask.render_template('logged_out.html')


@app.route('/login')
def login():
    redirect_uri = flask.url_for('auth', _external=True)
    return oauth.svipe.authorize_redirect(redirect_uri)


@app.route('/logout')
def logout():
    metadata = oauth.svipe.load_server_metadata()
    if id_token := flask.session.get('id_token'):
        requests.get(metadata.get('end_session_endpoint'), params={
            'id_token_hint':            id_token,
        })
    flask.session.pop('userinfo', None)
    flask.session.pop('id_token', None)
    return flask.redirect('/')


@app.route('/auth')
def auth():
    if tokenResponse := oauth.svipe.authorize_access_token():
        flask.session['userinfo'] = tokenResponse.get('userinfo')
        flask.session['id_token'] = tokenResponse.get('id_token')
    return flask.redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
