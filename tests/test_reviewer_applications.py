import sys
import types
import pytest
from io import BytesIO
from flask import send_file
from werkzeug.security import generate_password_hash
from config import Config
Config.SQLALCHEMY_DATABASE_URI = 'sqlite://'
Config.SQLALCHEMY_ENGINE_OPTIONS = Config.build_engine_options(Config.SQLALCHEMY_DATABASE_URI)

# Stubs to avoid optional deps
mercadopago_stub = types.ModuleType('mercadopago')
mercadopago_stub.SDK = lambda *a, **k: None
sys.modules.setdefault('mercadopago', mercadopago_stub)
utils_stub = types.ModuleType('utils')
taxa_service = types.ModuleType('utils.taxa_service')
taxa_service.calcular_taxa_cliente = lambda *a, **k: {'taxa_aplicada': 0, 'usando_taxa_diferenciada': False}
taxa_service.calcular_taxas_clientes = lambda *a, **k: []
utils_stub.taxa_service = taxa_service
utils_stub.preco_com_taxa = lambda *a, **k: 1
utils_stub.obter_estados = lambda *a, **k: []
utils_stub.external_url = lambda *a, **k: ''
utils_stub.gerar_comprovante_pdf = lambda *a, **k: ''
utils_stub.enviar_email = lambda *a, **k: None
utils_stub.formatar_brasilia = lambda *a, **k: ''
utils_stub.determinar_turno = lambda *a, **k: ''
sys.modules.setdefault('utils', utils_stub)
utils_security = types.ModuleType('utils.security')
utils_security.sanitize_input = lambda x: x
utils_security.password_is_strong = lambda x: True
sys.modules.setdefault('utils.security', utils_security)
utils_mfa = types.ModuleType('utils.mfa')
utils_mfa.mfa_required = lambda f: f
sys.modules.setdefault('utils.mfa', utils_mfa)
sys.modules.setdefault('utils.taxa_service', taxa_service)
pdf_service_stub = types.ModuleType('services.pdf_service')
pdf_service_stub.gerar_pdf_respostas = lambda *a, **k: None
pdf_service_stub.gerar_comprovante_pdf = lambda *a, **k: ''
pdf_service_stub.gerar_certificados_pdf = lambda *a, **k: ''
pdf_service_stub.gerar_certificado_personalizado = lambda *a, **k: ''
pdf_service_stub.gerar_pdf_comprovante_agendamento = lambda *a, **k: ''
pdf_service_stub.gerar_pdf_inscritos_pdf = lambda *a, **k: ''
pdf_service_stub.gerar_lista_frequencia_pdf = lambda *a, **k: ''
pdf_service_stub.gerar_pdf_feedback = lambda *a, **k: ''
pdf_service_stub.gerar_etiquetas = lambda *a, **k: send_file(BytesIO(b''), download_name='x.pdf')
pdf_service_stub.gerar_lista_frequencia = lambda *a, **k: send_file(BytesIO(b''), download_name='x.pdf')
pdf_service_stub.gerar_certificados = lambda *a, **k: send_file(BytesIO(b''), download_name='x.pdf')
pdf_service_stub.gerar_evento_qrcode_pdf = lambda *a, **k: send_file(BytesIO(b''), download_name='x.pdf')
pdf_service_stub.gerar_qrcode_token = lambda *a, **k: send_file(BytesIO(b''), download_name='x.png')
pdf_service_stub.gerar_programacao_evento_pdf = lambda *a, **k: send_file(BytesIO(b''), download_name='x.pdf')
pdf_service_stub.gerar_placas_oficinas_pdf = lambda *a, **k: send_file(BytesIO(b''), download_name='x.pdf')
pdf_service_stub.exportar_checkins_pdf_opcoes = lambda *a, **k: send_file(BytesIO(b''), download_name='x.pdf')
pdf_service_stub.gerar_revisor_details_pdf = lambda *a, **k: send_file(BytesIO(b''), download_name='x.pdf')
sys.modules.setdefault('services.pdf_service', pdf_service_stub)
arquivo_utils_stub = types.ModuleType('utils.arquivo_utils')
arquivo_utils_stub.arquivo_permitido = lambda *a, **k: True
sys.modules.setdefault('utils.arquivo_utils', arquivo_utils_stub)

from app import create_app
from extensions import db, login_manager
from models import (
    Usuario,
    Cliente,
    ReviewerApplication,
    Formulario,
    CampoFormulario,
    RevisorProcess,
    RevisorCandidatura,
    Evento,
)
from routes.auth_routes import auth_routes

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        cliente = Cliente(nome='Cli', email='cli@test', senha=generate_password_hash('123'))
        admin = Usuario(nome='Admin', cpf='1', email='admin@test', senha=generate_password_hash('123'), formacao='x', tipo='admin')
        user = Usuario(nome='User', cpf='2', email='user@test', senha=generate_password_hash('123'), formacao='x')
        db.session.add_all([cliente, admin, user])
        db.session.commit()
        db.session.add(ReviewerApplication(usuario_id=user.id))
        db.session.commit()
        def gerar_etiquetas_route(cliente_id):
            return ''

        app.add_url_rule(
            '/gerar_etiquetas/<int:cliente_id>',
            endpoint='routes.gerar_etiquetas_route',
            view_func=gerar_etiquetas_route,
        )
        def gerar_placas_oficinas(evento_id):
            return ''

        app.add_url_rule(
            '/gerar_placas_oficinas/<int:evento_id>',
            endpoint='routes.gerar_placas_oficinas',
            view_func=gerar_placas_oficinas,
        )
        def exportar_checkins_filtrados():
            return ''

        app.add_url_rule(
            '/exportar_checkins_filtrados',
            endpoint='routes.exportar_checkins_filtrados',
            view_func=exportar_checkins_filtrados,
        )
    yield app

@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, senha):
    return client.post('/login', data={'email': email, 'senha': senha}, follow_redirects=True)


def test_dashboard_applications_visible_for_cliente(client, app):
    login(client, 'cli@test', '123')
    resp = client.get('/dashboard_cliente')
    assert resp.status_code == 200
    assert 'processo seletivo de revisores'.encode() in resp.data.lower()


def test_update_application_requires_permission(client, app):
    with app.app_context():
        rid = ReviewerApplication.query.first().id

    login(client, 'user@test', '123')
    resp = client.post(f'/reviewer_applications/{rid}', data={'action': 'advance'}, follow_redirects=True)
    assert b'dashboard' in resp.data
    with app.app_context():
        assert ReviewerApplication.query.get(rid).stage == 'novo'

    login(client, 'cli@test', '123')
    resp = client.post(f'/reviewer_applications/{rid}', data={'action': 'advance'}, follow_redirects=True)
    assert resp.status_code in (200, 302)
    with app.app_context():
        assert ReviewerApplication.query.get(rid).stage == 'triagem'

def test_submit_application_and_visibility(client, app):
    with app.app_context():
        new_user = Usuario(
            nome='Applicant', cpf='3', email='app@test',
            senha=generate_password_hash('123'), formacao='x'
        )
        db.session.add(new_user)
        db.session.commit()
        uid = new_user.id
    login(client, 'app@test', '123')
    resp = client.post('/reviewer_applications/new', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Candidatura Recebida' in resp.data
    with app.app_context():
        assert ReviewerApplication.query.filter_by(usuario_id=uid).count() == 1
    login(client, 'cli@test', '123')
    resp = client.get('/dashboard_cliente')
    assert resp.status_code == 200


def test_revisor_approval_without_email(client, app):
    """Candidaturas sem email devem ser aprovadas sem criar usuario."""
    with app.app_context():
        cliente = Cliente.query.filter_by(email='cli@test').first()
        form = Formulario(nome='Form', cliente_id=cliente.id)
        db.session.add(form)
        db.session.commit()
        event = Evento(
            cliente_id=cliente.id,
            nome='E1',
            inscricao_gratuita=True,
            publico=True,
        )
        db.session.add(event)
        db.session.commit()
        form.eventos.append(event)
        db.session.commit()
        campo_nome = CampoFormulario(formulario_id=form.id, nome='nome', tipo='text')
        db.session.add(campo_nome)
        db.session.commit()
        proc = RevisorProcess(cliente_id=cliente.id, formulario_id=form.id, num_etapas=1)
        db.session.add(proc)
        db.session.commit()
        campo_id = campo_nome.id
        proc_id = proc.id

    client.post(f'/revisor/apply/{proc_id}', data={str(campo_id): 'NoEmail'})
    with app.app_context():
        cand = RevisorCandidatura.query.filter_by(nome='NoEmail').first()
        cand_id = cand.id

    login(client, 'cli@test', '123')
    resp = client.post(f'/revisor/approve/{cand_id}', json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success']
    assert 'reviewer_id' not in data
    with app.app_context():
        cand = RevisorCandidatura.query.get(cand_id)
        assert cand.status == 'aprovado'


def test_duplicate_application_redirects(client, app):
    login(client, 'user@test', '123')
    resp = client.post('/reviewer_applications/new', follow_redirects=True)
    assert resp.status_code == 200
    assert 'já foi registrada'.encode() in resp.data
    with app.app_context():
        user = Usuario.query.filter_by(email='user@test').first()
        assert ReviewerApplication.query.filter_by(usuario_id=user.id).count() == 1
