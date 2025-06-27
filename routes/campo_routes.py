from flask import render_template, Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import CampoPersonalizadoCadastro

campo_routes = Blueprint('campo_routes', __name__)

@campo_routes.route('/adicionar_campo_personalizado', methods=['POST'])
@login_required
def adicionar_campo_personalizado():
    if not (current_user.is_cliente() or getattr(current_user, 'tipo', None) == 'admin'):
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard_routes.dashboard_cliente'))
    nome_campo = request.form.get('nome_campo')
    tipo_campo = request.form.get('tipo_campo')
    obrigatorio = bool(request.form.get('obrigatorio'))

    novo_campo = CampoPersonalizadoCadastro(
        cliente_id=current_user.id,
        nome=nome_campo,
        tipo=tipo_campo,
        obrigatorio=obrigatorio
    )
    db.session.add(novo_campo)
    db.session.commit()

    flash('Campo personalizado adicionado com sucesso!', 'success')
    return redirect(url_for('dashboard_routes.dashboard_cliente'))

@campo_routes.route('/remover_campo_personalizado/<int:campo_id>', methods=['POST'])
@login_required
def remover_campo_personalizado(campo_id):
    if not (current_user.is_cliente() or getattr(current_user, 'tipo', None) == 'admin'):
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard_routes.dashboard_cliente'))

    campo = CampoPersonalizadoCadastro.query.get_or_404(campo_id)

    if campo.cliente_id != current_user.id and getattr(current_user, 'tipo', None) != 'admin':
        flash('Você não tem permissão para remover este campo.', 'danger')
        return redirect(url_for('dashboard_routes.dashboard_cliente'))

    db.session.delete(campo)
    db.session.commit()

    flash('Campo personalizado removido com sucesso!', 'success')
    return redirect(url_for('dashboard_routes.dashboard_cliente'))


@campo_routes.route('/toggle_obrigatorio_campo/<int:campo_id>', methods=['POST'])
@login_required
def toggle_obrigatorio_campo(campo_id):
    """Alterna a obrigatoriedade de um campo personalizado de cadastro."""
    if not (current_user.is_cliente() or getattr(current_user, 'tipo', None) == 'admin'):
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard_routes.dashboard_cliente'))

    campo = CampoPersonalizadoCadastro.query.get_or_404(campo_id)

    if campo.cliente_id != current_user.id and getattr(current_user, 'tipo', None) != 'admin':
        flash('Você não tem permissão para alterar este campo.', 'danger')
        return redirect(url_for('dashboard_routes.dashboard_cliente'))

    campo.obrigatorio = not campo.obrigatorio
    db.session.commit()

    flash('Campo atualizado com sucesso!', 'success')
    return redirect(url_for('dashboard_routes.dashboard_cliente'))






@campo_routes.route('/preview_cadastro')
@login_required
def preview_cadastro():
    """Mostra uma prévia do formulário de cadastro de participante."""
    if not (current_user.is_cliente() or getattr(current_user, 'tipo', None) == 'admin'):
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard_routes.dashboard_cliente'))

    from models import Evento, EventoInscricaoTipo, ConfiguracaoCliente
    from utils import preco_com_taxa

    evento = Evento.query.filter_by(cliente_id=current_user.id).first()

    campos = CampoPersonalizadoCadastro.query.filter_by(cliente_id=current_user.id).all()
    tipos_inscricao = []
    mostrar_taxa = True

    if evento:
        tipos_inscricao = EventoInscricaoTipo.query.filter_by(evento_id=evento.id).all()
        config_cli = ConfiguracaoCliente.query.filter_by(cliente_id=current_user.id).first()
        mostrar_taxa = config_cli.mostrar_taxa if config_cli else True

    return render_template(
        'auth/cadastro_preview.html',
        token='preview',
        evento=evento,
        sorted_keys=[],
        grouped_oficinas={},
        ministrantes=[],
        patrocinadores=[],
        campos_personalizados=campos,
        lote_vigente=None,
        lote_stats=None,
        lotes_ativos=[],
        tipos_inscricao=tipos_inscricao,
        mostrar_taxa=mostrar_taxa,
        preco_com_taxa=preco_com_taxa,
        solicitar_senha=False,
        cliente_id=current_user.id,
        disable_submit=True
    )

