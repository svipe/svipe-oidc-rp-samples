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

import  fastapi
from    fastapi.staticfiles                     import StaticFiles
from    fastapi.templating                      import Jinja2Templates
from    starlette.middleware.sessions           import SessionMiddleware
from    authlib.integrations.starlette_client   import OAuth

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

oauth = OAuth()
oauth.register(
    name                = 'svipe',
    client_id           = config.get('client_id'),
    client_secret       = config.get('client_secret'),
    server_metadata_url = f"{config.get('issuer')}/.well-known/openid-configuration",
    client_kwargs       = client_kwargs,
)


@app.get('/')
async def index(request: fastapi.Request):
    if userinfo := request.session.get('userinfo'):
        return templates.TemplateResponse('logged_in.html', {
            'request'  : request,
            'userinfo' : userinfo
        })
    else:
        return templates.TemplateResponse('logged_out.html', {
            'request'  : request
        })


@app.get('/login')
async def login(request: fastapi.Request):
    redirect_uri = request.url_for('auth')
    return await oauth.svipe.authorize_redirect(request, redirect_uri)


@app.get('/logout')
async def logout(request: fastapi.Request):
    metadata = await oauth.svipe.load_server_metadata()
    if id_token := request.session.get('id_token'):
        requests.get(metadata.get('end_session_endpoint'), params={
            'id_token_hint': id_token,
        })
    request.session.pop('userinfo', None)
    request.session.pop('id_token', None)
    return fastapi.responses.RedirectResponse(url='/')


@app.get('/auth')
async def auth(request: fastapi.Request):
    if tokenResponse := await oauth.svipe.authorize_access_token(request):
        request.session['userinfo'] = tokenResponse.get('userinfo')
        request.session['id_token'] = tokenResponse.get('id_token')
    return fastapi.responses.RedirectResponse(url='/')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
