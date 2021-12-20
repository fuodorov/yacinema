from flask import Blueprint, jsonify
from flasgger import swag_from

from core import config


roles_api = Blueprint('roles', __name__)


@roles_api.route('/', methods=['GET'])
@swag_from(config.DOCS_DIR.joinpath('roles').joinpath('get_roles.yml'))
def get_roles():
    return jsonify('success')


@roles_api.route('/', methods=['POST'])
@swag_from(config.DOCS_DIR.joinpath('roles').joinpath('add_new_role.yml'))
def add_new_role():
    return jsonify(msg='sucess')


@roles_api.route('/', methods=['PATCH'])
@swag_from(config.DOCS_DIR.joinpath('roles').joinpath('patch_role.yml'))
def patch_role():
    return jsonify(msg='success')


@roles_api.route('/', methods=['DELETE'])
@swag_from(config.DOCS_DIR.joinpath('roles').joinpath('delete_role.yml'))
def delete_role():
    return jsonify(msg='success')
