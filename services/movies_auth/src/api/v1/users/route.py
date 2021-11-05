from flask import Blueprint, jsonify
from flasgger import swag_from

from core import config


users_api = Blueprint('users', __name__)


@users_api.route('<user_id>/roles', methods=['GET'])
@swag_from(config.DOCS_DIR.joinpath('users').joinpath('get_user_roles.yml'))
def get_user_roles(user_id):
    return jsonify('success')


@users_api.route('<user_id>/roles', methods=['POST'])
@swag_from(config.DOCS_DIR.joinpath('users').joinpath('add_role_to_user.yml'))
def add_role_to_user(user_id):
    return jsonify(msg='success')


@users_api.route('<user_id>/roles', methods=['DELETE'])
@swag_from(config.DOCS_DIR.joinpath('users').joinpath('delete_user_role.yml'))
def delete_user_role(user_id):
    return jsonify(msg='success')


@users_api.route('<user_id>/superuser', methods=['GET'])
@swag_from(config.DOCS_DIR.joinpath('users').joinpath('super_user.yml'))
def super_user(user_id):
    return jsonify(msg='success')


@users_api.route('<user_id>/revoke_access_keys', methods=['GET'])
@swag_from(config.DOCS_DIR.joinpath('users').joinpath('revoke_access_keys.yml'))
def revoke_access_keys(user_id):
    return jsonify(msg='success')
