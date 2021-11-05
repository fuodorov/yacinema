from flask import Flask
from flasgger import Swagger

from api.v1 import auth_api, account_api, roles_api, users_api
from core.config import DOCS_DIR


app = Flask(__name__)
app.register_blueprint(auth_api, url_prefix='/auth/api/v1/auth')
app.register_blueprint(account_api, url_prefix='/auth/api/v1/account')
app.register_blueprint(roles_api, url_prefix='/auth/api/v1/roles')
app.register_blueprint(users_api, url_prefix='/auth/api/v1/users')


swagger = Swagger()
swagger.config['url_prefix'] = '/auth'
swagger.template_file = DOCS_DIR.joinpath('template.yml').as_posix()
swagger.init_app(app)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
