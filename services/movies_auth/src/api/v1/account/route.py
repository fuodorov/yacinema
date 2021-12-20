from flask import Blueprint, jsonify
from flasgger import swag_from

from core import config


account_api = Blueprint('account', __name__)


@account_api.route('/login', methods=['PATCH'])
@swag_from(config.DOCS_DIR.joinpath('account').joinpath('patch_login.yml'))
def patch_login():
    return jsonify(msg='success')


@account_api.route('/password', methods=['PATCH'])
@swag_from(config.DOCS_DIR.joinpath('account').joinpath('patch_password.yml'))
def patch_password():
    return jsonify(msg='success')


@account_api.route('/signin_history', methods=['GET'])
@swag_from(config.DOCS_DIR.joinpath('account').joinpath('signin_history.yml'))
def signin_history():
    return jsonify(msg='success')
