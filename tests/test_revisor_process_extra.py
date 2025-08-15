import os
from datetime import date, timedelta
import pytest
from werkzeug.security import generate_password_hash
from config import Config
Config.SQLALCHEMY_DATABASE_URI = 'sqlite://'
Config.SQLALCHEMY_ENGINE_OPTIONS = Config.build_engine_options(Config.SQLALCHEMY_DATABASE_URI)

from flask import Flask
from extensions import db, login_manager, migrate
from flask_migrate import upgrade

from models import Cliente, Formulario, RevisorProcess, Evento
from routes.revisor_routes import revisor_routes

@pytest.fixture
def app():
    templates_path = os.path.join(os.path.dirname(__file__), '..', 'templates')
    app = Flask(__name__, template_folder=templates_path)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = Config.build_engine_options('sqlite://')
    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(revisor_routes)
    with app.app_context():
        try:
            upgrade(revision="heads")
        except SystemExit:
            db.create_all()
        c1 = Cliente(nome='C1', email='c1@test', senha=generate_password_hash('123'))
        c2 = Cliente(nome='C2', email='c2@test', senha=generate_password_hash('123'))
        db.session.add_all([c1, c2])
        db.session.commit()
        f1 = Formulario(nome='F1', cliente_id=c1.id)
        f2 = Formulario(nome='F2', cliente_id=c2.id)
        db.session.add_all([f1, f2])
        db.session.commit()
        e1 = Evento(cliente_id=c1.id, nome='E1', inscricao_gratuita=True, publico=True)
        e2 = Evento(cliente_id=c2.id, nome='E2', inscricao_gratuita=True, publico=True)
        db.session.add_all([e1, e2])
        db.session.commit()

        e1.formularios.append(f1)
        e2.formularios.append(f2)
        db.session.commit()
        db.session.add(
            RevisorProcess(
                cliente_id=c1.id,
                formulario_id=f1.id,
                num_etapas=1,
                availability_start=date.today() - timedelta(days=1),
                availability_end=date.today() + timedelta(days=1),
                exibir_para_participantes=True,
            )


        proc1 = RevisorProcess(
            cliente_id=c1.id,
            formulario_id=f1.id,
            num_etapas=1,
            availability_start=date.today() - timedelta(days=1),
            availability_end=date.today() + timedelta(days=1),
            exibir_para_participantes=True,
            eventos=[e1],

        )
        proc2 = RevisorProcess(
            cliente_id=c2.id,
            formulario_id=f2.id,
            num_etapas=1,
            availability_start=date.today() - timedelta(days=3),
            availability_end=date.today() - timedelta(days=1),
            exibir_para_participantes=True,
            eventos=[e2],
        )
        proc3 = RevisorProcess(
            cliente_id=c1.id,
            formulario_id=f1.id,
            num_etapas=1,
            exibir_para_participantes=False,

        )
        db.session.add_all([proc1, proc2, proc3])
        db.session.commit()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()


def test_process_creation_with_dates(app):
    with app.app_context():
        proc = RevisorProcess.query.filter_by(exibir_para_participantes=True).first()
        assert proc.availability_start is not None
        assert proc.availability_end is not None
        start = proc.availability_start.date() if hasattr(proc.availability_start, 'date') else proc.availability_start
        end = proc.availability_end.date() if hasattr(proc.availability_end, 'date') else proc.availability_end
        assert start <= date.today() <= end



def test_visibility_flag_filters(app):
    with app.app_context():
        visible = (
            RevisorProcess.query
            .join(RevisorProcess.formulario)
            .join(Formulario.eventos)
            .filter(RevisorProcess.exibir_para_participantes.is_(True))
            .all()
        )
        hidden = (
            RevisorProcess.query
            .join(RevisorProcess.formulario)
            .join(Formulario.eventos)
            .filter(RevisorProcess.exibir_para_participantes.is_(False))
            .all()
        )
        assert len(visible) == 2
        assert len(hidden) == 1


def test_eligible_events_route(client, app):
    resp = client.get('/revisor/eligible_events')
    assert resp.status_code == 200
    data = resp.get_json()
    with app.app_context():
        e1 = Evento.query.filter_by(nome='E1').first()
    assert data == [{'id': e1.id, 'nome': 'E1'}]


def test_config_route_saves_availability(client, app):
    with app.app_context():
        cliente = Cliente.query.filter_by(email='c1@test').first()
        formulario = Formulario.query.filter_by(cliente_id=cliente.id).first()
        start = date.today()
        end = start + timedelta(days=2)

        from flask_login import login_user, logout_user

        with client:
            with app.test_request_context():
                login_user(cliente)
            resp = client.post(
                '/config_revisor',
                data={
                    'formulario_id': formulario.id,
                    'num_etapas': 1,
                    'stage_name': ['Etapa 1'],
                    'availability_start': start.strftime('%Y-%m-%d'),
                    'availability_end': end.strftime('%Y-%m-%d'),
                    'exibir_participantes': 'on',
                },
            )
            with app.test_request_context():
                logout_user()

        assert resp.status_code in (302, 200)
        proc = RevisorProcess.query.filter_by(cliente_id=cliente.id).first()
        assert proc.availability_start.date() == start
        assert proc.availability_end.date() == end

