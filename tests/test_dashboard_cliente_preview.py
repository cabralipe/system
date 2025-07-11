import pytest
from werkzeug.security import generate_password_hash
from config import Config
from app import create_app
from extensions import db
from models import Usuario, Cliente, Evento

Config.SQLALCHEMY_DATABASE_URI = 'sqlite://'
Config.SQLALCHEMY_ENGINE_OPTIONS = Config.build_engine_options(Config.SQLALCHEMY_DATABASE_URI)

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    with app.app_context():
        db.create_all()
        cliente = Cliente(nome='Cli', email='cli@test', senha=generate_password_hash('123'))
        db.session.add(cliente)
        db.session.commit()
        Evento(cliente_id=cliente.id, nome='EV')
        db.session.commit()
        Usuario(id=cliente.id, nome='CliUser', cpf='1', email='cli@test', senha=generate_password_hash('123'), formacao='x', tipo='cliente')
        db.session.commit()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, senha):
    return client.post('/login', data={'email': email, 'senha': senha}, follow_redirects=True)


def test_preview_evento_button_present(client, app):
    login(client, 'cli@test', '123')
    resp = client.get('/dashboard_cliente')
    assert resp.status_code == 200
    assert b'id="previewEventoBtn"' in resp.data
