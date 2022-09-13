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
import urllib

import  fastapi
from    fastapi.staticfiles                     import StaticFiles
from    fastapi.templating                      import Jinja2Templates
from    starlette.middleware.sessions           import SessionMiddleware

os.chdir(pathlib.Path(__file__).parent)

config_file = pathlib.Path('../config.yaml')
config_info = yaml.safe_load(config_file.read_text())
if not (config_name := sys.argv[-1]) in config_info:
    config_name = 'default'
config = config_info.get(config_name)

app = fastapi.FastAPI()
session_secret = secrets.token_urlsafe(32)
app.add_middleware(SessionMiddleware, secret_key=session_secret)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


client_kwargs = {'scope': config.get('scope')}
if config.get('pkce') == True:
    client_kwargs['code_challenge_method'] = 'S256'


def oidc_load_server_metadata(config):
    server_metadata_url = f"{config.get('issuer')}/.well-known/openid-configuration"
    resp = requests.get(server_metadata_url)
    if resp.status_code == 200:
        return resp.json()

openid_config = oidc_load_server_metadata(config)


def oidc_get_tokeninfo(code, code_verifier):
    params = {
        'code'              : code,
        'grant_type'        : 'authorization_code',
        'redirect_uri'      : '/auth'
    }
    if code_verifier:
        params['code_verifier'] = code_verifier
    else:
        params['client_secret'] = config.get('client_secret')

    resp = requests.post(openid_config.get('token_endpoint'), data=params)
    if resp.status_code == 200:
        return resp.json()

def oidc_get_userinfo(access_token):
    resp = requests.post(
        openid_config.get('userinfo_endpoint'), data = {
            'access_token' : access_token,
        }
    )
    if resp.status_code == 200:
        return resp.json()

def oidc_logout(id_token):
    requests.get(openid_config.get('end_session_endpoint'), params={
        'id_token_hint': id_token,
    })

def oidc_create_code_challenge(code_verifier):
    import hashlib, base64
    code_verifier_hashed = hashlib.sha256(code_verifier.encode())
    code_challenge       = base64.urlsafe_b64encode(code_verifier_hashed.digest())
    code_challenge       = code_challenge.decode().rstrip('=')
    return code_challenge


@app.get('/')
async def index(request: fastapi.Request):
    if userinfo := request.session.get('userinfo'):
        return templates.TemplateResponse('logged_in.html', {
            "request": request,
            "userinfo": userinfo
        })
    else:
        request.session['state'] = secrets.token_urlsafe(16)
        request.session['nonce'] = secrets.token_urlsafe(16)
        auth_session = '.'.join(
            [config.get('client_id')] +
            [request.session.get(x) for x in ['state', 'nonce']
        ])
        if config.get('pkce'):
            request.session['code_verifier']  = secrets.token_urlsafe(16)
            auth_session = '.'.join([
                auth_session,
                oidc_create_code_challenge(request.session['code_verifier']),
                'S256'
            ])

        return templates.TemplateResponse('logged_out.html', {
            'request'      : request,
            'auth_server'  :'/'.join(config.get('issuer').split('/')[:3]),
            'auth_session' : auth_session,
        })


@app.get('/logout')
async def logout(request: fastapi.Request):
    if id_token := request.session.get('id_token'):
        oidc_logout(id_token)
    request.session.pop('userinfo',   None)
    request.session.pop('id_token',   None)
    return fastapi.responses.RedirectResponse(url='/')


@app.get('/auth')
async def auth(request: fastapi.Request):
    params =  dict(urllib.parse.parse_qsl(request.url.query))
    if params.get('state') == request.session.get('state'):
        if tokenResponse := oidc_get_tokeninfo(
            params.get('code'),
            request.session.get('code_verifier')
            ):
            if userinfo := oidc_get_userinfo(tokenResponse.get('access_token')):
                request.session['id_token'] = tokenResponse.get('id_token')
                request.session['userinfo'] = userinfo
                for entry in ['state', 'nonce', 'code_verifier']:
                    request.session.pop(entry, None)

    return fastapi.responses.RedirectResponse(url='/')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
