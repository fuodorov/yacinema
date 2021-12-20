from flask import Blueprint, jsonify
from flasgger import swag_from

from core import config


auth_api = Blueprint('auth', __name__)


@auth_api.route('/login', methods=['POST'])
@swag_from(config.DOCS_DIR.joinpath('auth').joinpath('login.yml'))
def login():
    return jsonify(msg='success')


@auth_api.route('/signup', methods=['POST'])
@swag_from(config.DOCS_DIR.joinpath('auth').joinpath('signup.yml'))
def signup():
    return jsonify(msg='success')


@auth_api.route('/refresh', methods=['POST'])
@swag_from(config.DOCS_DIR.joinpath('auth').joinpath('refresh.yml'))
def refresh():
    return jsonify(msg='success')


@auth_api.route('/logout', methods=['POST'])
@swag_from(config.DOCS_DIR.joinpath('auth').joinpath('logout.yml'))
def logout():
    return jsonify(msg='success')


@auth_api.route('/logout_all_accounts', methods=['POST'])
@swag_from(config.DOCS_DIR.joinpath('auth').joinpath('logout_all_accounts.yml'))
def logout_all_accounts():
    return jsonify(msg='success')


@auth_api.route('/access_check', methods=['GET'])
@swag_from(config.DOCS_DIR.joinpath('auth').joinpath('access_check.yml'))
def access_check():
    return jsonify(msg='success')
