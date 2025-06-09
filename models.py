import os
import uuid
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db  # Se você inicializa o SQLAlchemy em 'extensions.py'
from sqlalchemy.orm import relationship  # Adicione esta linha!
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email


# =================================
#             CLIENTE
# =================================
class EditarClienteForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    senha = PasswordField('Nova Senha')
    submit = SubmitField('Salvar Alterações')
# =================================
#             USUÁRIO
# =================================
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    formacao = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default='participante')
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)  # ✅ Alterado para permitir NULL
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=True)  # Novo campo para associar usuário ao evento
    tipo_inscricao_id = db.Column(db.Integer, db.ForeignKey('evento_inscricao_tipo.id'), nullable=True)

    tipo_inscricao = db.relationship('EventoInscricaoTipo', backref=db.backref('usuarios', lazy=True))
    cliente = db.relationship('Cliente', backref=db.backref('usuarios', lazy=True))
    evento = db.relationship('Evento', backref=db.backref('usuarios', lazy=True))
    # NOVOS CAMPOS PARA LOCAIS DE ATUAÇÃO:
    estados = db.Column(db.String(255), nullable=True)   # Ex.: "SP,RJ,MG"
    cidades = db.Column(db.String(255), nullable=True)   # Ex.: "São Paulo,Rio de Janeiro,Belo Horizonte"

    def verificar_senha(self, senha):
        return check_password_hash(self.senha, senha)

    def __repr__(self):
        return f"<Usuario {self.nome}>"
    
    def is_superuser(self):
        return self.tipo == "superadmin"

    def is_cliente(self):
        return self.tipo == "cliente"
    
    def is_professor(self):
         return self.tipo == 'professor'
    
    def tem_pagamento_pendente(self):
        pendente = Inscricao.query.filter_by(
            usuario_id=self.id,
            status_pagamento="pending"
        ).count()
        return pendente > 0




# =================================
#           CONFIGURAÇÃO
# =================================
class Configuracao(db.Model):
    __tablename__ = 'configuracao'

    id = db.Column(db.Integer, primary_key=True)
    permitir_checkin_global = db.Column(db.Boolean, default=False)
    habilitar_feedback = db.Column(db.Boolean, default=False)
    habilitar_certificado_individual = db.Column(db.Boolean, default=False)
    
    taxa_percentual_inscricao = db.Column(db.Numeric(5,2), default=0)

    def __repr__(self):
        return f"<Configuracao permitir_checkin_global={self.permitir_checkin_global}>"


# =================================
#          MINISTRANTE
# =================================

# Tabela de associação N:N
oficina_ministrantes_association = db.Table(
    'oficina_ministrantes_association',
    db.Column('oficina_id', db.Integer, db.ForeignKey('oficina.id'), primary_key=True),
    db.Column('ministrante_id', db.Integer, db.ForeignKey('ministrante.id'), primary_key=True)
)


class Ministrante(db.Model, UserMixin):
    __tablename__ = 'ministrante'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    formacao = db.Column(db.String(255), nullable=False)
    categorias_formacao = db.Column(db.String(512), nullable=True)  # Nova coluna para múltiplas categorias
    foto = db.Column(db.String(255), nullable=True)  # Nova coluna para armazenar caminho da foto
    areas_atuacao = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=False)
    pix = db.Column(db.String(255), nullable=False)
    cidade = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    cliente = db.relationship("Cliente", backref="ministrantes")

    @property
    def tipo(self):
        return 'ministrante'

    def __repr__(self):
        return f"<Ministrante {self.nome}>"


# ... (outras importações permanecem iguais)

# =================================
#             OFICINA
# =================================
class Oficina(db.Model):
    __tablename__ = 'oficina'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    ministrante_id = db.Column(db.Integer, db.ForeignKey('ministrante.id'), nullable=True)
    ministrante_obj = db.relationship("Ministrante", backref="oficinas", lazy=True)
  
    # Tipo de inscrição: 'sem_inscricao', 'com_inscricao_sem_limite', 'com_inscricao_com_limite'
    tipo_inscricao = db.Column(db.String(30), nullable=False, default='com_inscricao_com_limite')
    # Tipo de oficina: 'Oficina', 'Palestra', 'Conferência', etc.
    tipo_oficina = db.Column(db.String(50), nullable=True)
    # Campo para quando o tipo_oficina for 'outros'
    tipo_oficina_outro = db.Column(db.String(100), nullable=True)
    vagas = db.Column(db.Integer, nullable=False)
    carga_horaria = db.Column(db.String(10), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    qr_code = db.Column(db.String(255), nullable=True)

    opcoes_checkin = db.Column(db.String(255), nullable=True)  # Ex: "palavra1,palavra2,palavra3,palavra4,palavra5"
    palavra_correta = db.Column(db.String(50), nullable=True)
    
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)  # ✅ Adicionado
    cliente = db.relationship("Cliente", back_populates="oficinas")  # ✅ Corrigido para `back_populates`
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=True)
    evento = db.relationship("Evento", backref=db.backref('oficinas', lazy=True))
    
    ministrantes_associados = db.relationship(
        "Ministrante",
        secondary="oficina_ministrantes_association",  # nome da tabela que criamos
        backref="oficinas_relacionadas",
        lazy='dynamic'  # ou 'select', 'joined', etc. conforme sua preferência
    )

    dias = db.relationship('OficinaDia', back_populates="oficina", lazy=True, cascade="all, delete-orphan")

    # Novo campo: Se True, inscrição gratuita; se False, será necessário realizar pagamento.
    inscricao_gratuita = db.Column(db.Boolean, default=True)

    # 🔥 Corrigido o método __init__
    def __init__(self, titulo, descricao, ministrante_id, vagas, carga_horaria, estado, cidade, cliente_id=None, evento_id=None, qr_code=None, opcoes_checkin=None, palavra_correta=None, tipo_inscricao='com_inscricao_com_limite', tipo_oficina='Oficina', tipo_oficina_outro=None):
        self.titulo = titulo
        self.descricao = descricao
        self.ministrante_id = ministrante_id
        self.carga_horaria = carga_horaria
        self.estado = estado
        self.cidade = cidade
        self.qr_code = qr_code
        self.cliente_id = cliente_id
        self.evento_id = evento_id
        self.opcoes_checkin = opcoes_checkin
        self.palavra_correta = palavra_correta
        self.tipo_inscricao = tipo_inscricao
        self.tipo_oficina = tipo_oficina
        self.tipo_oficina_outro = tipo_oficina_outro
        
        # Define o valor de vagas com base no tipo de inscrição
        if tipo_inscricao == 'sem_inscricao':
            self.vagas = 0  # Não é necessário controlar vagas
        elif tipo_inscricao == 'com_inscricao_sem_limite':
            self.vagas = 9999  # Um valor alto para representar "sem limite"
        else:  # com_inscricao_com_limite
            self.vagas = vagas

    def __repr__(self):
        return f"<Oficina {self.titulo}>"


# =================================
#          OFICINA DIA
# =================================
class OficinaDia(db.Model):
    __tablename__ = 'oficinadia'

    id = db.Column(db.Integer, primary_key=True)
    oficina_id = db.Column(db.Integer, db.ForeignKey('oficina.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    horario_inicio = db.Column(db.String(5), nullable=False)
    horario_fim = db.Column(db.String(5), nullable=False)
    palavra_chave_manha = db.Column(db.String(50), nullable=True)
    palavra_chave_tarde = db.Column(db.String(50), nullable=True)

    oficina = db.relationship('Oficina', back_populates="dias")

    def __repr__(self):
        return f"<OficinaDia {self.data} {self.horario_inicio}-{self.horario_fim}>"


# =================================
#           INSCRIÇÃO
# =================================


class Inscricao(db.Model):
    __tablename__ = 'inscricao'
    
     # 👉 NOVOS CAMPOS
    payment_id = db.Column(db.String(64), index=True, nullable=True)       # id da transação no MP
    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                           index=True, nullable=False)
    
    boleto_url      = db.Column(db.String(512), nullable=True)   # ← NOVO

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    oficina_id = db.Column(db.Integer, db.ForeignKey('oficina.id'), nullable=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=True)
    
    qr_code_token = db.Column(db.String(100), unique=True, nullable=True)
    checkin_attempts = db.Column(db.Integer, default=0)
    
    tipo_inscricao_id = db.Column(db.Integer, db.ForeignKey('inscricao_tipo.id'), nullable=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote_inscricao.id'), nullable=True)
    
    usuario = db.relationship('Usuario', backref=db.backref('inscricoes', lazy='joined'))
    oficina = db.relationship('Oficina', backref='inscritos')
    evento = db.relationship('Evento', backref='inscricoes')
    lote = db.relationship('LoteInscricao', backref=db.backref('inscricoes', lazy=True))
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    status_pagamento = db.Column(
        db.String(20),
        default="pending",
        index=True        # ➊  (gera índice)
    )

    def __init__(self, usuario_id, cliente_id, oficina_id=None, evento_id=None, status_pagamento="pending"):
        self.usuario_id = usuario_id
        self.cliente_id = cliente_id
        self.oficina_id = oficina_id
        self.evento_id = evento_id
        self.status_pagamento = status_pagamento

        # Gera um token único garantido
        while True:
            token = str(uuid.uuid4())
            existing = Inscricao.query.filter_by(qr_code_token=token).first()
            if not existing:
                self.qr_code_token = token
                break

    def __repr__(self):
        return f"<Inscricao Usuario={self.usuario_id}, Oficina={self.oficina_id}, Evento={self.evento_id}>"

    

# Novo modelo para tipos de inscrição (caso a oficina seja paga)
class InscricaoTipo(db.Model):
    __tablename__ = 'inscricao_tipo'
    
    id = db.Column(db.Integer, primary_key=True)
    oficina_id = db.Column(db.Integer, db.ForeignKey('oficina.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=True)  # Ex: Estudante, Professor
    preco = db.Column(db.Numeric(10,2), nullable=True)
    
    oficina = db.relationship('Oficina', backref=db.backref('tipos_inscricao', lazy=True))
    
    def __repr__(self):
        return f"<InscricaoTipo {self.nome}: R$ {self.preco}>"


# Em models.py ou onde você define seus modelos

class EventoInscricaoTipo(db.Model):
    __tablename__ = 'evento_inscricao_tipo'

    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)

    # Relação com Evento - removendo backref para evitar conflito

    def __init__(self, evento_id, nome, preco):
        self.evento_id = evento_id
        self.nome = nome
        self.preco = preco


class RegraInscricaoEvento(db.Model):
    __tablename__ = 'regra_inscricao_evento'

    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    tipo_inscricao_id = db.Column(db.Integer, db.ForeignKey('evento_inscricao_tipo.id'), nullable=False)
    limite_oficinas = db.Column(db.Integer, nullable=False, default=0)  # 0 = sem limite
    oficinas_permitidas = db.Column(db.Text, nullable=True)  # IDs das oficinas separados por vírgula

    evento = db.relationship('Evento', backref=db.backref('regras_inscricao', lazy=True))
    tipo_inscricao = db.relationship('EventoInscricaoTipo', backref=db.backref('regras', lazy=True))

    def __init__(self, evento_id, tipo_inscricao_id, limite_oficinas=0, oficinas_permitidas=None):
        self.evento_id = evento_id
        self.tipo_inscricao_id = tipo_inscricao_id
        self.limite_oficinas = limite_oficinas
        self.oficinas_permitidas = oficinas_permitidas

    def get_oficinas_permitidas_list(self):
        if not self.oficinas_permitidas:
            return []
        return [int(id) for id in self.oficinas_permitidas.split(',') if id]

    def set_oficinas_permitidas_list(self, oficinas_ids):
        self.oficinas_permitidas = ','.join(str(id) for id in oficinas_ids)


# =================================
#            CHECKIN
# =================================

class Checkin(db.Model):
    __tablename__ = 'checkin'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    oficina_id = db.Column(db.Integer, db.ForeignKey('oficina.id'), nullable=True)  # agora pode ser nulo
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=True)    # novo campo
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    palavra_chave = db.Column(db.String(50), nullable=False)
    
     # NOVO  ▼▼▼
    cliente_id  = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    cliente     = db.relationship('Cliente', backref=db.backref('checkins', lazy=True))

    usuario = db.relationship('Usuario', backref=db.backref('checkins', lazy=True))
    oficina = db.relationship('Oficina', backref=db.backref('checkins', lazy=True))
    evento = db.relationship('Evento', backref=db.backref('checkins_evento', lazy=True))

    def __repr__(self):
        return f"<Checkin (usuario={self.usuario_id}, oficina={self.oficina_id}, evento={self.evento_id}, data={self.data_hora})>"

# =================================
#            FEEDBACK
# =================================
class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    ministrante_id = db.Column(db.Integer, db.ForeignKey('ministrante.id'), nullable=True)
    oficina_id = db.Column(db.Integer, db.ForeignKey('oficina.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Nota de 1 a 5
    comentario = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref='feedbacks')
    ministrante = db.relationship('Ministrante', backref='feedbacks')
    oficina = db.relationship('Oficina', backref='feedbacks')

    def __repr__(self):
        return f"<Feedback id={self.id} " \
               f"Usuario={self.usuario_id if self.usuario_id else 'N/A'} " \
               f"Ministrante={self.ministrante_id if self.ministrante_id else 'N/A'} " \
               f"Oficina={self.oficina_id}>"


# =================================
#       MATERIAL DA OFICINA
# =================================
class MaterialOficina(db.Model):
    __tablename__ = 'material_oficina'

    id = db.Column(db.Integer, primary_key=True)
    oficina_id = db.Column(db.Integer, db.ForeignKey('oficina.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    oficina = db.relationship('Oficina', backref='materiais')

    def __repr__(self):
        return f"<MaterialOficina id={self.id}, arquivo={self.nome_arquivo}>"
    


# =================================
#       RELATÓRIO DA OFICINA
# =================================
class RelatorioOficina(db.Model):
    __tablename__ = 'relatorio_oficina'

    id = db.Column(db.Integer, primary_key=True)
    oficina_id = db.Column(db.Integer, db.ForeignKey('oficina.id'), nullable=False)
    ministrante_id = db.Column(db.Integer, db.ForeignKey('ministrante.id'), nullable=False)

    metodologia = db.Column(db.Text, nullable=True)
    resultados = db.Column(db.Text, nullable=True)
    fotos_videos_path = db.Column(db.String(255), nullable=True)
    enviado_em = db.Column(db.DateTime, default=datetime.utcnow)

    oficina = db.relationship(
        'Oficina',
        backref=db.backref('relatorios_oficina', lazy=True)
    )
    ministrante = db.relationship(
        'Ministrante',
        backref=db.backref('relatorios_ministrante', lazy=True)
    )

    def __repr__(self):
        return f"<RelatorioOficina oficina_id={self.oficina_id} ministrante_id={self.ministrante_id}>"

class Cliente(db.Model, UserMixin):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False) 
    ativo = db.Column(db.Boolean, default=True)  # Habilitação pelo superusuário
    tipo = db.Column(db.String(20), default='cliente')  # Define o tipo do usuário
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)  # ✅ Adicionando relação com Cliente

    # Campo novo para pagamento:
    habilita_pagamento = db.Column(db.Boolean, default=False)

     # Relacionamento com Oficina
    oficinas = db.relationship("Oficina", back_populates="cliente")  # ✅ Agora usa `back_populates`
    
    configuracao = db.relationship('ConfiguracaoCliente', back_populates='cliente', uselist=False)
    
    # Novos campos (caminho das imagens):
    logo_certificado = db.Column(db.String(255), nullable=True)       # Logo
    fundo_certificado = db.Column(db.String(255), nullable=True)      # Fundo do certificado
    assinatura_certificado = db.Column(db.String(255), nullable=True) # Assinatura
    texto_personalizado = db.Column(db.Text)

    
    def is_active(self):
        """Retorna True se o cliente está ativo."""
        return self.ativo
    def get_id(self):
        """Retorna o ID do cliente como string, necessário para Flask-Login."""
        return str(self.id)
    def is_cliente(self):
        return self.tipo == 'cliente'

class LinkCadastro(db.Model):
    __tablename__ = 'link_cadastro'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=True)
    slug_customizado = db.Column(db.String(50), unique=True, nullable=True)
    token = db.Column(db.String(36), unique=True, nullable=False, default=str(uuid.uuid4()))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship('Cliente', backref=db.backref('links_cadastro', lazy=True))
    evento = db.relationship('Evento', backref=db.backref('links_cadastro', lazy=True))

    def __repr__(self):
        return f"<LinkCadastro cliente_id={self.cliente_id}, evento_id={self.evento_id}, token={self.token}, slug={self.slug_customizado}>"
    

from extensions import db

class Formulario(db.Model):
    __tablename__ = 'formularios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)  # Se cada cliente puder ter seus próprios formulários
    
    cliente = db.relationship('Cliente', backref=db.backref('formularios', lazy=True))
    campos = db.relationship('CampoFormulario', backref='formulario', lazy=True, cascade="all, delete-orphan")
    # Relacionamento com respostas do formulário.
    respostas = db.relationship('RespostaFormulario', back_populates='formulario', cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Formulario {self.nome}>"

class CampoFormulario(db.Model):
    __tablename__ = 'campos_formulario'

    id = db.Column(db.Integer, primary_key=True)
    formulario_id = db.Column(db.Integer, db.ForeignKey('formularios.id'), nullable=True, default=1)  # Atualizado: permite NULL e default 1
    nome = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    opcoes = db.Column(db.Text, nullable=True)
    obrigatorio = db.Column(db.Boolean, default=False)
    tamanho_max = db.Column(db.Integer, nullable=True)
    regex_validacao = db.Column(db.String(255), nullable=True)
    descricao = db.Column(db.Text, nullable=True)  # Novo campo conforme banco do Render

    def __repr__(self):
        return f"<Campo {self.nome} ({self.tipo})>"


class RespostaFormulario(db.Model):
    __tablename__ = 'respostas_formulario'

    id = db.Column(db.Integer, primary_key=True)
    formulario_id = db.Column(db.Integer, db.ForeignKey('formularios.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_submissao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # NOVA COLUNA PARA STATUS
    status_avaliacao = db.Column(db.String(50), nullable=True, default='Não Avaliada')
    
    respostas_campos = db.relationship('RespostaCampo', back_populates='resposta_formulario', cascade="all, delete-orphan")

    formulario = db.relationship('Formulario', back_populates='respostas')  # 🔄 Corrigido o back_populates
    usuario = db.relationship('Usuario', backref=db.backref('respostas', lazy=True))

    def __repr__(self):
        return f"<RespostaFormulario ID {self.id} - Formulário {self.formulario_id} - Usuário {self.usuario_id}>"

class RespostaCampo(db.Model):
    __tablename__ = 'respostas_campo'

    id = db.Column(db.Integer, primary_key=True)
    resposta_formulario_id = db.Column(db.Integer, db.ForeignKey('respostas_formulario.id'), nullable=False)
    campo_id = db.Column(db.Integer, db.ForeignKey('campos_formulario.id'), nullable=False)
    valor = db.Column(db.Text, nullable=False)

    resposta_formulario = db.relationship('RespostaFormulario', back_populates='respostas_campos')
    campo = db.relationship('CampoFormulario', backref=db.backref('respostas', lazy=True))

    def __repr__(self):
        return f"<RespostaCampo ID {self.id} - Campo {self.campo_id} - Valor {self.valor}>"
    
# models.py
class ConfiguracaoCliente(db.Model):
    __tablename__ = 'configuracao_cliente'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    permitir_checkin_global = db.Column(db.Boolean, default=False)
    habilitar_feedback = db.Column(db.Boolean, default=False)
    habilitar_certificado_individual = db.Column(db.Boolean, default=False)
    
    # Campo para habilitar credenciamento via QRCode do evento:
    habilitar_qrcode_evento_credenciamento = db.Column(db.Boolean, default=False)
    
    # Relacionamento com o cliente (opcional se quiser acessar .cliente)
    cliente = db.relationship('Cliente', back_populates='configuracao')
    
    habilitar_submissao_trabalhos = db.Column(db.Boolean, default=False)

    
    
class FeedbackCampo(db.Model):
    __tablename__ = 'feedback_campo'

    id = db.Column(db.Integer, primary_key=True)
    resposta_campo_id = db.Column(db.Integer, db.ForeignKey('respostas_campo.id'), nullable=False)
    
    ministrante_id = db.Column(db.Integer, db.ForeignKey('ministrante.id'), nullable=True)
    cliente_id     = db.Column(db.Integer, db.ForeignKey('cliente.id'),    nullable=True)
    
    texto_feedback = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    resposta_campo = db.relationship('RespostaCampo', backref=db.backref('feedbacks_campo', lazy=True))
    ministrante = db.relationship('Ministrante', backref=db.backref('feedbacks_campo', lazy=True))
    cliente     = db.relationship('Cliente',    backref=db.backref('feedbacks_campo', lazy=True))


    def __repr__(self):
        return f"<FeedbackCampo id={self.id} resposta_campo={self.resposta_campo_id} ministrante={self.ministrante_id}>"

# =================================
#            PROPOSTA
# =================================
class Proposta(db.Model):
    __tablename__ = 'proposta'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    tipo_evento = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Proposta {self.id} de {self.nome}>"

# =================================
#            EVENTO
# =================================

class Evento(db.Model):
        __tablename__ = 'evento'

        id = db.Column(db.Integer, primary_key=True)
        cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
        nome = db.Column(db.String(255), nullable=False)
        descricao = db.Column(db.Text, nullable=True)
        banner_url = db.Column(db.String(255), nullable=True)
        programacao = db.Column(db.Text, nullable=True)
        localizacao = db.Column(db.String(255), nullable=True)
        link_mapa = db.Column(db.Text, nullable=True)
        inscricao_gratuita = db.Column(db.Boolean, default=False, nullable=False)  # Novo campo
        # Novos campos de data
        data_inicio = db.Column(db.DateTime, nullable=True)
        data_fim = db.Column(db.DateTime, nullable=True)
        hora_inicio = db.Column(db.Time, nullable=True)
        hora_fim = db.Column(db.Time, nullable=True)
        
        # Adicione aqui a coluna status
        status = db.Column(db.String(50), default='ativo')
        
        capacidade_padrao = db.Column(db.Integer, nullable=True, default=0)
        requer_aprovacao = db.Column(db.Boolean, default=False)
        publico = db.Column(db.Boolean, default=True)

        habilitar_lotes = db.Column(db.Boolean, default=False)

        cliente = db.relationship('Cliente', backref=db.backref('eventos', lazy=True))
        # Modificando o relacionamento para evitar conflito de backref
        tipos_inscricao = db.relationship(
            "EventoInscricaoTipo", 
            backref="evento", 
            overlaps="evento"
        )
        
        @property
        def tipos_inscricao_evento(self):
            """Propriedade para compatibilidade com os templates existentes"""
            return self.tipos_inscricao

        def get_regras_inscricao(self, tipo_inscricao_id):
            """Retorna as regras de inscrição para um tipo específico de inscrição"""
            for regra in self.regras_inscricao:
                if regra.tipo_inscricao_id == tipo_inscricao_id:
                    return regra
            return None
        
        def get_data_formatada(self):
            if self.data_inicio:
                if self.data_fim and self.data_fim != self.data_inicio:
                    return f"{self.data_inicio.strftime('%d/%m/%Y')} - {self.data_fim.strftime('%d/%m/%Y')}"
                return self.data_inicio.strftime('%d/%m/%Y')
            return "Data a definir"
    
        def get_preco_base(self):
            if self.tipos_inscricao:
                return min(tipo.preco for tipo in self.tipos_inscricao)
            return 0


class FormularioTemplate(db.Model):
    __tablename__ = 'formulario_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    categoria = db.Column(db.String(100), nullable=True)  # e.g., "workshop", "event", "course"
    is_default = db.Column(db.Boolean, default=False)
    
    cliente = db.relationship('Cliente', backref=db.backref('templates_formulario', lazy=True))
    campos = db.relationship('CampoFormularioTemplate', backref='template', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FormularioTemplate {self.nome}>"

class CampoFormularioTemplate(db.Model):
    __tablename__ = 'campos_formulario_template'

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('formulario_templates.id'), nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    opcoes = db.Column(db.Text, nullable=True)
    obrigatorio = db.Column(db.Boolean, default=False)
    ordem = db.Column(db.Integer, default=0)  # For ordering fields
    
    def __repr__(self):
        return f"<CampoFormularioTemplate {self.nome} ({self.tipo})>"
    
from datetime import datetime, timedelta
from extensions import db

class ConfiguracaoAgendamento(db.Model):
    """Configuração de regras para agendamentos de visitas por cliente."""
    __tablename__ = 'configuracao_agendamento'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    
    # Regras de agendamento
    prazo_cancelamento = db.Column(db.Integer, nullable=False, default=24)  # Horas antes do evento
    tempo_bloqueio = db.Column(db.Integer, nullable=False, default=7)  # Dias de bloqueio por violação
    capacidade_padrao = db.Column(db.Integer, nullable=False, default=30)  # Quantidade padrão de alunos por horário
    intervalo_minutos = db.Column(db.Integer, nullable=False, default=60)  # Minutos entre agendamentos
    
    # Horários de disponibilidade
    horario_inicio = db.Column(db.Time, nullable=False)
    horario_fim = db.Column(db.Time, nullable=False)
    dias_semana = db.Column(db.String(20), nullable=False, default="1,2,3,4,5")  # 0=Dom, 1=Seg, ..., 6=Sáb
    
    # Relações
    cliente = db.relationship('Cliente', backref=db.backref('configuracoes_agendamento', lazy=True))
    evento = db.relationship('Evento', backref=db.backref('configuracoes_agendamento', lazy=True))
    
    def __repr__(self):
        return f"<ConfiguracaoAgendamento {self.id} - Evento {self.evento_id}>"


class SalaVisitacao(db.Model):
    """Salas disponíveis para visitação em um evento."""
    __tablename__ = 'sala_visitacao'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    capacidade = db.Column(db.Integer, nullable=False, default=30)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    
    # Relações
    evento = db.relationship('Evento', backref=db.backref('salas_visitacao', lazy=True))
    
    def __repr__(self):
        return f"<SalaVisitacao {self.nome} - Evento {self.evento_id}>"


class HorarioVisitacao(db.Model):
    """Slots de horários disponíveis para agendamento."""
    __tablename__ = 'horario_visitacao'
    
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    horario_inicio = db.Column(db.Time, nullable=False)
    horario_fim = db.Column(db.Time, nullable=False)
    capacidade_total = db.Column(db.Integer, nullable=False)
    vagas_disponiveis = db.Column(db.Integer, nullable=False)
    
    # Relações
    evento = db.relationship('Evento', backref=db.backref('horarios_visitacao', lazy=True))
    
    def __repr__(self):
        return f"<HorarioVisitacao {self.data} {self.horario_inicio}-{self.horario_fim} ({self.vagas_disponiveis} vagas)>"


class AgendamentoVisita(db.Model):
    """Agendamento realizado por um professor para uma turma."""
    __tablename__ = 'agendamento_visita'
    
    id = db.Column(db.Integer, primary_key=True)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario_visitacao.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Informações da escola e turma
    escola_nome = db.Column(db.String(200), nullable=False)
    escola_codigo_inep = db.Column(db.String(20), nullable=True)
    turma = db.Column(db.String(50), nullable=False)
    nivel_ensino = db.Column(db.String(50), nullable=False)  # Anos iniciais, finais, etc.
    quantidade_alunos = db.Column(db.Integer, nullable=False)
    
    # Status do agendamento
    data_agendamento = db.Column(db.DateTime, default=datetime.utcnow)
    data_cancelamento = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='confirmado')  # confirmado, cancelado, realizado
    checkin_realizado = db.Column(db.Boolean, default=False)
    data_checkin = db.Column(db.DateTime, nullable=True)
    
    # QR Code para check-in
    qr_code_token = db.Column(db.String(100), unique=True, nullable=False)
    
    # Salas selecionadas para visitação
    salas_selecionadas = db.Column(db.String(200), nullable=True)  # IDs separados por vírgula
    
    # Relações
    horario = db.relationship('HorarioVisitacao', backref=db.backref('agendamentos', lazy=True))
    professor = db.relationship('Usuario', backref=db.backref('agendamentos_visitas', lazy=True))
    
    def __init__(self, **kwargs):
        super(AgendamentoVisita, self).__init__(**kwargs)
        import uuid
        self.qr_code_token = str(uuid.uuid4())
    
    def __repr__(self):
        return f"<AgendamentoVisita {self.id} - Prof. {self.professor.nome} - {self.escola_nome}>"


class AlunoVisitante(db.Model):
    """Alunos participantes de uma visita agendada."""
    __tablename__ = 'aluno_visitante'
    
    id = db.Column(db.Integer, primary_key=True)
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamento_visita.id'), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=True)  # Opcional para menores
    presente = db.Column(db.Boolean, default=False)
    
    # Relações
    agendamento = db.relationship('AgendamentoVisita', backref=db.backref('alunos', lazy=True))
    
    def __repr__(self):
        return f"<AlunoVisitante {self.nome} - Agendamento {self.agendamento_id}>"


class ProfessorBloqueado(db.Model):
    """Registro de professores bloqueados por violação de regras."""
    __tablename__ = 'professor_bloqueado'
    
    id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    data_inicial = db.Column(db.DateTime, default=datetime.utcnow)
    data_final = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    
    # Relações
    professor = db.relationship('Usuario', backref=db.backref('bloqueios', lazy=True))
    evento = db.relationship('Evento', backref=db.backref('professores_bloqueados', lazy=True))
    
    def __repr__(self):
        return f"<ProfessorBloqueado {self.professor_id} até {self.data_final.strftime('%d/%m/%Y')}>"
    

class Patrocinador(db.Model):
    __tablename__ = 'patrocinador'
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    logo_path = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  # Ex: 'Realização', 'Patrocínio', etc.
    
    evento = db.relationship('Evento', backref=db.backref('patrocinadores', lazy=True))

    def __init__(self, evento_id, logo_path, categoria):
        self.evento_id = evento_id
        self.logo_path = logo_path
        self.categoria = categoria

class CertificadoTemplate(db.Model):
    __tablename__ = 'certificado_template'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)  # HTML ou texto estruturado
    ativo = db.Column(db.Boolean, default=False)

    cliente = db.relationship("Cliente", backref="certificados_templates")


class CampoPersonalizadoCadastro(db.Model):
    __tablename__ = 'campos_personalizados_cadastro'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # texto, número, email, data, etc.
    obrigatorio = db.Column(db.Boolean, default=False)

    cliente = db.relationship('Cliente', backref=db.backref('campos_personalizados', lazy=True))

class TrabalhoCientifico(db.Model):
    __tablename__ = 'trabalhos_cientificos'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    resumo = db.Column(db.Text, nullable=True)
    arquivo_pdf = db.Column(db.String(255), nullable=True)
    area_tematica = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default="submetido")  # Ex: submetido, em avaliação, aceito, rejeitado, revisando
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)

class AvaliacaoTrabalho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trabalho_id = db.Column(db.Integer, db.ForeignKey('trabalhos_cientificos.id'), nullable=False)
    avaliador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nota = db.Column(db.Float, nullable=True)
    conceito = db.Column(db.String(20), nullable=True)
    estrelas = db.Column(db.Integer, nullable=True)
    comentario = db.Column(db.Text)
    status = db.Column(db.String(20), default='avaliado')

class ApresentacaoTrabalho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trabalho_id = db.Column(db.Integer, db.ForeignKey('trabalhos_cientificos.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    horario = db.Column(db.String(5), nullable=False)
    local = db.Column(db.String(100), nullable=True)


class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    tipo_inscricao_id = db.Column(db.Integer, db.ForeignKey('evento_inscricao_tipo.id'), nullable=False)
    status = db.Column(db.String(50), default="pendente")
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    mercado_pago_id = db.Column(db.String(255), nullable=True)

    usuario = db.relationship("Usuario")
    evento = db.relationship("Evento")
    tipo_inscricao = db.relationship("EventoInscricaoTipo")



# Tabela de associação para múltiplos ganhadores por sorteio
sorteio_ganhadores = db.Table('sorteio_ganhadores',
    db.Column('sorteio_id', db.Integer, db.ForeignKey('sorteio.id'), primary_key=True),
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
)


class Sorteio(db.Model):
    __tablename__ = 'sorteio'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    premio = db.Column(db.String(255), nullable=False)
    data_sorteio = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=True)
    oficina_id = db.Column(db.Integer, db.ForeignKey('oficina.id'), nullable=True)
    ganhador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)  # Mantido para compatibilidade
    num_vencedores = db.Column(db.Integer, default=1)  # Número de vencedores do sorteio
    status = db.Column(db.String(20), default='pendente')  # pendente, realizado, cancelado
    
    # Relacionamentos
    cliente = db.relationship('Cliente', backref=db.backref('sorteios', lazy=True))
    evento = db.relationship('Evento', backref=db.backref('sorteios', lazy=True))
    oficina = db.relationship('Oficina', backref=db.backref('sorteios', lazy=True))
    ganhador = db.relationship('Usuario', backref=db.backref('sorteios_ganhos', lazy=True))  # Mantido para compatibilidade
    
    # Nova relação para múltiplos ganhadores
    ganhadores = db.relationship('Usuario', secondary='sorteio_ganhadores', lazy='subquery',
                                  backref=db.backref('sorteios_vencidos', lazy=True))

    def __repr__(self):
        return f"<Sorteio {self.titulo} - Prêmio: {self.premio}>"



class LoteInscricao(db.Model):
    __tablename__ = 'lote_inscricao'

    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=True)
    data_fim = db.Column(db.DateTime, nullable=True)
    qtd_maxima = db.Column(db.Integer, nullable=True)  # Limite de inscrições
    ordem = db.Column(db.Integer, nullable=False, default=0)  # Para ordenar lotes
    ativo = db.Column(db.Boolean, default=True)

    # Relacionamento com o evento
    evento = db.relationship('Evento', backref=db.backref('lotes', lazy=True, order_by='LoteInscricao.ordem'))

    def __repr__(self):
        return f"<LoteInscricao {self.nome}>"
    
    def is_valid(self):
        """Verifica se o lote está válido (dentro da data ou limite de inscritos)"""
        now = datetime.utcnow()
        
        # Verificar por data
        if self.data_inicio and self.data_fim:
            if now < self.data_inicio or now > self.data_fim:
                return False
        
        # Verificar por quantidade de inscrições
        if self.qtd_maxima is not None:
            count = Inscricao.query.filter_by(
                evento_id=self.evento_id, 
                lote_id=self.id
            ).count()
            if count >= self.qtd_maxima:
                return False
        
        return True
    
class LoteTipoInscricao(db.Model):
    __tablename__ = 'lote_tipo_inscricao'

    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lote_inscricao.id'), nullable=False)
    tipo_inscricao_id = db.Column(db.Integer, db.ForeignKey('evento_inscricao_tipo.id'), nullable=False)
    preco = db.Column(db.Float, nullable=False)

    # Relacionamentos
    lote = db.relationship('LoteInscricao', backref=db.backref('tipos_inscricao', lazy=True))
    tipo_inscricao = db.relationship('EventoInscricaoTipo', backref=db.backref('lotes_precos', lazy=True))

    def __repr__(self):
        return f"<LoteTipoInscricao Lote={self.lote_id}, Tipo={self.tipo_inscricao_id}, Preço={self.preco}>"
