"""
Populate Script para o Sistema de Eventos e Inscrições
Este script gera dados de teste abrangentes para o sistema de eventos.

DESCRIÇÃO:
-----------
Este script cria centenas de registros de teste incluindo:
- Clientes (organizadores de eventos)
- Eventos com diferentes configurações
- Ministrantes
- Oficinas e palestras
- Usuários (participantes, professores, clientes, administradores)
- Inscrições em eventos e oficinas
- Checkins
- Feedbacks
- Agendamentos de visitas escolares
- Lotes de inscrição
- Tipos de inscrição com preços variados
- Sorteios e patrocinadores

INSTRUÇÕES DE USO:
------------------
1. Certifique-se de que o ambiente virtual está ativado
2. Certifique-se de ter instalado todas as dependências:
   pip install faker

3. Execute dentro do contexto do seu aplicativo Flask:
   
   from app import app, db
   from populate_script import popular_banco
   
   with app.app_context():
       dados = popular_banco()
       
4. Se quiser limpar o banco antes de popular, descomente as linhas
   relacionadas ao comando "SET FOREIGN_KEY_CHECKS" na função popular_banco()

PERSONALIZAÇÃO:
---------------
- Ajuste as quantidades modificando os parâmetros nas chamadas de função
- Modifique as listas de constantes para personalizar os valores gerados
"""
import os
import sys
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from faker import Faker
import uuid
import bcrypt
import pytest
from unittest.mock import Mock
from slugify import slugify  # You may need to pip install python-slugify
from sqlalchemy.exc import IntegrityError

# Assumindo que o app flask está inicializado em outro arquivo
# Você precisará importar seus modelos e extensões
# Modifique estes caminhos conforme necessário
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importe suas extensões e modelos
from extensions import db
from models import (
    Cliente,
    Usuario,
    Evento,
    EventoInscricaoTipo,
    InscricaoTipo,
    Oficina,
    OficinaDia,
    Ministrante,
    Inscricao,
    RegraInscricaoEvento,
    Checkin,
    Feedback,
    LinkCadastro,
    ConfiguracaoCliente,
    LoteInscricao,
    LoteTipoInscricao,
    ConfiguracaoAgendamento,
    SalaVisitacao,
    HorarioVisitacao,
    AgendamentoVisita,
    AlunoVisitante,
    CertificadoTemplate,
    MaterialOficina,
    Sorteio,
    Pagamento,
    Patrocinador,
    oficina_ministrantes_association,
    Submission,
    Review,
    Assignment,
    AuditLog,
    ArquivoBinario,
)

# Inicialize o Faker
fake = Faker('pt_BR')
Faker.seed(42)  # Para resultados consistentes

# Constantes e listas para geração de dados
ESTADOS_BRASIL = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

TIPOS_FORMACAO = [
    'Graduação', 'Pós-graduação', 'Mestrado', 'Doutorado', 
    'Especialização', 'Técnico', 'Ensino Médio'
]

TIPOS_OFICINA = [
    'Oficina', 'Palestra', 'Conferência', 'Workshop', 
    'Mesa redonda', 'Seminário', 'Curso', 'Minicurso'
]

TIPOS_USUARIO = [
    'participante', 'professor', 'cliente', 'superadmin', 'ministrante'
]

AREAS_ATUACAO = [
    'Educação', 'Tecnologia', 'Saúde', 'Artes', 'Ciências', 
    'Engenharia', 'Humanidades', 'Negócios', 'Direito'
]

STATUS_PAGAMENTO = ['pending', 'approved', 'rejected', 'cancelled']

def criar_clientes(quantidade=5):
    """Cria clientes no sistema"""
    clientes = []
    for i in range(quantidade):
        email = fake.unique.company_email()
        while Cliente.query.filter_by(email=email).first():
            fake.unique.clear()
            email = fake.unique.company_email()

        cliente = Cliente(
            nome=fake.company(),
            email=email,
            senha=generate_password_hash(fake.password()),
            ativo=True,
            habilita_pagamento=random.choice([True, False])
        )
        db.session.add(cliente)
        
        # Criar configuração para o cliente
        config = ConfiguracaoCliente(
            cliente=cliente,
            permitir_checkin_global=random.choice([True, False]),
            habilitar_feedback=random.choice([True, False]),
            habilitar_certificado_individual=random.choice([True, False]),
            habilitar_qrcode_evento_credenciamento=random.choice([True, False]),
            habilitar_submissao_trabalhos=random.choice([True, False])
        )
        db.session.add(config)
        
        # Criar um template de certificado para o cliente
        template = CertificadoTemplate(
            cliente=cliente,
            titulo=f"Certificado Padrão - {cliente.nome}",
            conteudo=f"""
            <h1>CERTIFICADO</h1>
            <p>Certificamos que {{nome_participante}} participou do evento {{nome_evento}} 
            realizado por {cliente.nome} com carga horária de {{carga_horaria}} horas.</p>
            <p>Data: {{data_emissao}}</p>
            <p>Assinatura: ___________________</p>
            """,
            ativo=True
        )
        db.session.add(template)
        
        clientes.append(cliente)
    
    db.session.commit()
    fake.unique.clear()
    return clientes

def gerar_slug_unico(num_palavras=3, max_tentativas=10):
    """Gera um slug único consultando o banco antes de retornar."""
    for _ in range(max_tentativas):
        # Generate a slug from random words
        palavras = fake.words(num_palavras)
        slug = slugify(" ".join(palavras))
        
        # Check if slug exists
        if not LinkCadastro.query.filter_by(slug_customizado=slug).first():
            return slug
            
    # If we couldn't find a unique slug after max attempts, add UUID suffix
    return f"{slug}-{str(uuid.uuid4())[:8]}"

def criar_eventos(clientes, quantidade_por_cliente=5):
    """Cria eventos para cada cliente"""
    todos_eventos = []
    
    for cliente in clientes:
        for i in range(quantidade_por_cliente):
            # Define datas para o evento
            dias_evento = random.randint(1, 5)
            data_inicio = fake.date_between(start_date='-1y', end_date='+1y')
            data_fim = data_inicio + timedelta(days=dias_evento-1)
            
            # Status baseado na data
            hoje = datetime.now().date()
            if data_fim < hoje:
                status = 'encerrado'
            else:
                status = 'ativo'
            
            evento = Evento(
                cliente_id=cliente.id,
                nome=f"{fake.catch_phrase()} {random.choice(['2023', '2024', '2025'])}",
                descricao=fake.paragraph(nb_sentences=5),
                banner_url=f"banners/evento_{i}_{cliente.id}.jpg",
                programacao=fake.paragraph(nb_sentences=3),
                localizacao=fake.address(),
                link_mapa=f"https://maps.google.com/?q={fake.latitude()},{fake.longitude()}",
                data_inicio=data_inicio,
                data_fim=data_fim,
                hora_inicio=datetime.strptime(f"{random.randint(8, 10)}:00", "%H:%M").time(),
                hora_fim=datetime.strptime(f"{random.randint(16, 19)}:00", "%H:%M").time(),
                status=status,
                inscricao_gratuita=random.choice([True, False]),
                capacidade_padrao=random.randint(50, 500),
                requer_aprovacao=random.choice([True, False]),
                publico=random.choice([True, False]),
                habilitar_lotes=random.choice([True, False])
            )
            
            db.session.add(evento)
            db.session.flush()  # Para obter o ID
            
            # Criar patrocinadores simulados
            for _ in range(random.randint(2, 5)):
                patrocinador = Patrocinador(
                    evento_id=evento.id,
                    logo_path=f"logos/patrocinador_{uuid.uuid4()}.jpg",
                    categoria=random.choice(['Realização', 'Patrocínio', 'Apoio'])
                )
                db.session.add(patrocinador)
            
            # Criar tipos de inscrição para o evento
            criar_tipos_inscricao_evento(evento)
            
            # Se o evento tem lotes habilitados, criar lotes
            if evento.habilitar_lotes:
                criar_lotes_evento(evento)
            
            # Criar um link de cadastro para o evento
            slug = gerar_slug_unico()
            link = LinkCadastro(
                cliente_id=cliente.id,
                evento_id=evento.id,
                slug_customizado=slug,
                token=str(uuid.uuid4())
            )
            db.session.add(link)
            
            # Configura agendamento se for um evento educacional
            if random.choice([True, False]):
                config = ConfiguracaoAgendamento(
                    cliente_id=cliente.id,
                    evento_id=evento.id,
                    prazo_cancelamento=random.choice([24, 48, 72]),
                    tempo_bloqueio=random.choice([7, 14, 30]),
                    capacidade_padrao=random.randint(20, 50),
                    intervalo_minutos=random.choice([60, 90, 120]),
                    horario_inicio=datetime.strptime(f"{random.randint(8, 10)}:00", "%H:%M").time(),
                    horario_fim=datetime.strptime(f"{random.randint(16, 19)}:00", "%H:%M").time(),
                    dias_semana="1,2,3,4,5"
                )
                db.session.add(config)
                
                # Cria salas de visitação
                for j in range(random.randint(2, 5)):
                    sala = SalaVisitacao(
                        nome=f"Sala {j+1}",
                        descricao=fake.sentence(),
                        capacidade=random.randint(20, 40),
                        evento_id=evento.id
                    )
                    db.session.add(sala)
                
                # Cria horários de visitação
                for _ in range(random.randint(5, 10)):
                    data_horario = fake.date_between_dates(date_start=data_inicio, date_end=data_fim)
                    hora_inicio = datetime.strptime(f"{random.randint(8, 15)}:00", "%H:%M").time()
                    hora_fim = datetime.strptime(f"{hora_inicio.hour + 1}:00", "%H:%M").time()
                    
                    capacidade = random.randint(20, 50)
                    horario = HorarioVisitacao(
                        evento_id=evento.id,
                        data=data_horario,
                        horario_inicio=hora_inicio,
                        horario_fim=hora_fim,
                        capacidade_total=capacidade,
                        vagas_disponiveis=capacidade
                    )
                    db.session.add(horario)
            
            todos_eventos.append(evento)
            
            # Cria um sorteio para alguns eventos
            if random.choice([True, False]):
                sorteio = Sorteio(
                    titulo=f"Sorteio {fake.word().capitalize()}",
                    descricao=fake.paragraph(nb_sentences=2),
                    premio=fake.sentence(nb_words=6),
                    data_sorteio=fake.date_time_between(start_date=data_inicio, end_date=data_fim),
                    cliente_id=cliente.id,
                    evento_id=evento.id,
                    status=random.choice(['pendente', 'realizado', 'cancelado'])
                )
                db.session.add(sorteio)
    
    db.session.commit()
    return todos_eventos

def criar_tipos_inscricao_evento(evento):
    """Cria tipos de inscrição para um evento"""
    tipos = []
    categorias = ['Estudante', 'Professor', 'Profissional', 'Convidado']
    
    # Se o evento é gratuito, apenas um tipo de inscrição
    if evento.inscricao_gratuita:
        tipo = EventoInscricaoTipo(
            evento_id=evento.id,
            nome='Geral',
            preco=0.0
        )
        db.session.add(tipo)
        db.session.flush()
        tipos.append(tipo)
    else:
        # Vários tipos de inscrição com preços diferentes
        for categoria in random.sample(categorias, random.randint(2, len(categorias))):
            preco_base = random.randint(50, 300)
            # Desconto para estudantes e professores
            if categoria in ['Estudante', 'Professor']:
                preco = preco_base * 0.7
            elif categoria == 'Convidado':
                preco = 0.0
            else:
                preco = preco_base
                
            tipo = EventoInscricaoTipo(
                evento_id=evento.id,
                nome=categoria,
                preco=preco
            )
            db.session.add(tipo)
            db.session.flush()
            tipos.append(tipo)

            # Criar regras de inscrição para alguns tipos
            if random.choice([True, False]):
                regra = RegraInscricaoEvento(
                    evento_id=evento.id,
                    tipo_inscricao_id=tipo.id,
                    limite_oficinas=random.choice([0, 2, 3, 5])
                )
                db.session.add(regra)

    return tipos

def criar_lotes_evento(evento):
    """Cria lotes de inscrição para um evento"""
    tipos_inscricao = evento.tipos_inscricao
    
    # Criar 3 lotes: primeiro, segundo e terceiro
    data_base = evento.data_inicio - timedelta(days=90)
    
    lotes = []
    for i in range(3):
        data_inicio = data_base + timedelta(days=i*30)
        data_fim = data_inicio + timedelta(days=25)
        
        lote = LoteInscricao(
            evento_id=evento.id,
            nome=f"{i+1}º Lote",
            data_inicio=data_inicio,
            data_fim=data_fim,
            qtd_maxima=random.randint(50, 100),
            ordem=i+1,
            ativo=True
        )
        db.session.add(lote)
        db.session.flush()
        lotes.append(lote)
        
        # Criar preços para cada tipo de inscrição neste lote
        for tipo in tipos_inscricao:
            # Aumento progressivo de preço a cada lote (10%)
            preco_base = tipo.preco
            preco_lote = preco_base * (1 + i * 0.1)
            
            lote_tipo = LoteTipoInscricao(
                lote_id=lote.id,
                tipo_inscricao_id=tipo.id,
                preco=preco_lote
            )
            db.session.add(lote_tipo)
    
    return lotes

def criar_ministrantes(clientes, quantidade=20):
    """Cria ministrantes para as oficinas"""
    ministrantes = []
    
    for i in range(quantidade):
        cliente = random.choice(clientes)
        
        categorias = random.sample(TIPOS_FORMACAO, random.randint(1, 3))
        categorias_formacao = ','.join(categorias)
        
        areas = random.sample(AREAS_ATUACAO, random.randint(1, 3))
        areas_atuacao = ','.join(areas)
        
        ministrante = Ministrante(
            nome=fake.name(),
            formacao=random.choice(TIPOS_FORMACAO),
            categorias_formacao=categorias_formacao,
            foto=f"fotos/ministrante_{i}.jpg",
            areas_atuacao=areas_atuacao,
            cpf=fake.cpf(),
            pix=fake.email(),
            cidade=fake.city(),
            estado=random.choice(ESTADOS_BRASIL),
            email=fake.email(),
            senha=generate_password_hash(fake.password()),
            cliente_id=cliente.id
        )
        db.session.add(ministrante)
        ministrantes.append(ministrante)
    
    db.session.commit()
    return ministrantes

def criar_oficinas(eventos, ministrantes, quantidade_por_evento=10):
    """Cria oficinas para os eventos"""
    todas_oficinas = []
    
    for evento in eventos:
        # Seleciona ministrantes aleatórios para este evento
        evento_ministrantes = random.sample(ministrantes, min(len(ministrantes), quantidade_por_evento))
        
        for i, ministrante in enumerate(evento_ministrantes):
            # Decide se a oficina será grátis ou paga
            inscricao_gratuita = random.choice([True, False])
            
            # Tipos de inscrição
            tipo_inscricao = random.choice(['sem_inscricao', 'com_inscricao_sem_limite', 'com_inscricao_com_limite'])
            
            # Define vagas com base no tipo de inscrição
            if tipo_inscricao == 'sem_inscricao':
                vagas = 0
            elif tipo_inscricao == 'com_inscricao_sem_limite':
                vagas = 9999
            else:
                vagas = random.randint(20, 100)
            
            tipo_oficina = random.choice(TIPOS_OFICINA)
            tipo_oficina_outro = None
            if tipo_oficina == 'Outros':
                tipo_oficina_outro = fake.word().capitalize()
            
            # Cria oficina
            oficina = Oficina(
                titulo=fake.sentence(nb_words=6),
                descricao=fake.paragraph(nb_sentences=4),
                ministrante_id=ministrante.id,
                vagas=vagas,
                carga_horaria=f"{random.randint(2, 8)}h",
                estado=random.choice(ESTADOS_BRASIL),
                cidade=fake.city(),
                cliente_id=evento.cliente_id,
                evento_id=evento.id,
                qr_code=f"qrcode/oficina_{evento.id}_{i}.png",
                opcoes_checkin="palavra1,palavra2,palavra3,palavra4,palavra5",
                palavra_correta=f"palavra{random.randint(1, 5)}",
                tipo_inscricao=tipo_inscricao,
                tipo_oficina=tipo_oficina,
                tipo_oficina_outro=tipo_oficina_outro,
                inscricao_gratuita=inscricao_gratuita
            )
            db.session.add(oficina)
            db.session.flush()
            
            # Associa mais ministrantes a esta oficina (aleatoriamente)
            outros_ministrantes = random.sample(
                [m for m in ministrantes if m.id != ministrante.id], 
                random.randint(0, 2)
            )
            for outro_ministrante in outros_ministrantes:
                associacao = oficina_ministrantes_association.insert().values(
                    oficina_id=oficina.id,
                    ministrante_id=outro_ministrante.id
                )
                db.session.execute(associacao)
            
            # Cria dias para a oficina
            criar_dias_oficina(oficina, evento)
            
            # Se for oficina paga, criar tipos de inscrição
            if not inscricao_gratuita:
                criar_tipos_inscricao_oficina(oficina)
            
            # Adiciona materiais para algumas oficinas
            if random.choice([True, False]):
                for j in range(random.randint(1, 3)):
                    material = MaterialOficina(
                        oficina_id=oficina.id,
                        nome_arquivo=f"Material {j+1} - {oficina.titulo}.pdf",
                        caminho_arquivo=f"materiais/oficina_{oficina.id}_material_{j}.pdf"
                    )
                    db.session.add(material)
            
            todas_oficinas.append(oficina)
    
    db.session.commit()
    return todas_oficinas

def criar_dias_oficina(oficina, evento):
    """Cria dias para uma oficina, respeitando o período do evento"""
    # Determina quantos dias a oficina terá
    num_dias = random.randint(1, 3)
    
    # Se o evento tem datas definidas, usa-as como referência
    if evento.data_inicio and evento.data_fim:
        datas_possiveis = []
        data_atual = evento.data_inicio
        while data_atual <= evento.data_fim:
            datas_possiveis.append(data_atual)
            data_atual += timedelta(days=1)
        
        # Seleciona datas aleatórias para a oficina
        if len(datas_possiveis) >= num_dias:
            datas_selecionadas = random.sample(datas_possiveis, num_dias)
        else:
            datas_selecionadas = datas_possiveis
    else:
        # Se o evento não tem datas, cria datas aleatórias
        data_base = fake.date_between(start_date='-1m', end_date='+3m')
        datas_selecionadas = [data_base + timedelta(days=i) for i in range(num_dias)]
    
    # Cria os dias da oficina
    for data in datas_selecionadas:
        # Define horários aleatórios
        hora_inicio = random.randint(8, 14)
        duracao = random.randint(2, 4)
        
        dia = OficinaDia(
            oficina_id=oficina.id,
            data=data,
            horario_inicio=f"{hora_inicio:02d}:00",
            horario_fim=f"{hora_inicio + duracao:02d}:00",
            palavra_chave_manha=fake.word(),
            palavra_chave_tarde=fake.word()
        )
        db.session.add(dia)

def criar_tipos_inscricao_oficina(oficina):
    """Cria tipos de inscrição para oficinas pagas"""
    categorias = ['Estudante', 'Professor', 'Profissional']
    
    for categoria in random.sample(categorias, random.randint(1, len(categorias))):
        preco_base = random.randint(20, 100)
        
        # Descontos para certas categorias
        if categoria == 'Estudante':
            preco = preco_base * 0.6
        elif categoria == 'Professor':
            preco = preco_base * 0.8
        else:
            preco = preco_base
            
        tipo = InscricaoTipo(
            oficina_id=oficina.id,
            nome=categoria,
            preco=preco
        )
        db.session.add(tipo)

def criar_usuarios(clientes, quantidade=150):
    """Cria usuários para o sistema associando-os a clientes"""
    usuarios = []
    
    # Criar um superadmin
    superadmin = Usuario(
        nome="Administrador do Sistema",
        cpf=fake.cpf(),
        email="admin@sistema.com",
        senha=generate_password_hash("admin123"),
        formacao="Administrador de Sistemas",
        tipo="superadmin"
    )
    db.session.add(superadmin)
    usuarios.append(superadmin)
    
    # Criar usuários regulares
    for i in range(quantidade):
        # Define o tipo aleatoriamente, mas com maior probabilidade para participantes
        tipo = random.choices(
            TIPOS_USUARIO,
            weights=[0.7, 0.15, 0.1, 0.0, 0.05],
            k=1
        )[0]
        
        # Seleciona aleatoriamente estados e cidades
        num_estados = random.randint(1, 3)
        estados_usuario = random.sample(ESTADOS_BRASIL, num_estados)
        cidades_usuario = [fake.city() for _ in range(num_estados)]
        
        cliente = random.choice(clientes)

        usuario = Usuario(
            nome=fake.name(),
            cpf=fake.cpf(),
            email=fake.email(),
            senha=generate_password_hash(fake.password()),
            formacao=random.choice(TIPOS_FORMACAO),
            tipo=tipo,
            estados=','.join(estados_usuario),
            cidades=','.join(cidades_usuario),
            cliente_id=cliente.id
        )
        db.session.add(usuario)
        usuarios.append(usuario)
    
    db.session.commit()
    return usuarios

def criar_inscricoes(usuarios, eventos, oficinas):
    """Cria inscrições para usuários em eventos e oficinas"""
    # Filtra usuários que são participantes ou professores
    participantes = [u for u in usuarios if u.tipo in ('participante', 'professor')]
    
    inscricoes = []
    
    # Inscrições em eventos
    for evento in eventos:
        # Seleciona aleatoriamente usuários para inscrever neste evento
        num_inscritos = random.randint(10, min(len(participantes), 100))
        inscritos_evento = random.sample(participantes, num_inscritos)
        
        # Lista de tipos de inscrição disponíveis
        tipos_inscricao = evento.tipos_inscricao
        
        # Se o evento tem lotes, pega o lote ativo
        lotes_ativos = [l for l in evento.lotes if l.ativo]
        lote_atual = random.choice(lotes_ativos) if lotes_ativos else None
        
        for usuario in inscritos_evento:
            # Escolhe um tipo de inscrição aleatório
            tipo_inscricao = random.choice(tipos_inscricao) if tipos_inscricao else None
            
            # Define o status do pagamento
            # Eventos gratuitos sempre têm pagamento aprovado
            if evento.inscricao_gratuita:
                status = 'approved'
            else:
                status = random.choices(
                    STATUS_PAGAMENTO, 
                    weights=[0.2, 0.6, 0.1, 0.1], 
                    k=1
                )[0]
            
            # Cria a inscrição
            inscricao = Inscricao(
                usuario_id=usuario.id,
                cliente_id=evento.cliente_id,
                evento_id=evento.id,
                status_pagamento=status,
                tipo_inscricao_id=tipo_inscricao.id if tipo_inscricao else None,
                lote_id=lote_atual.id if lote_atual else None
            )
            db.session.add(inscricao)
            inscricoes.append(inscricao)
            
            # Adiciona informações de pagamento para inscrições pagas
            if not evento.inscricao_gratuita:
                payment_id = str(uuid.uuid4())
                inscricao.payment_id = payment_id
                
                # Para boletos, adiciona URL
                if random.choice([True, False]):
                    inscricao.boleto_url = f"https://exemplo.com/boletos/{payment_id}"
                
                # Cria registro de pagamento
                pagamento = Pagamento(
                    usuario_id=usuario.id,
                    evento_id=evento.id,
                    tipo_inscricao_id=tipo_inscricao.id if tipo_inscricao else 1,
                    status=status,
                    mercado_pago_id=f"MP-{uuid.uuid4()}"
                )
                db.session.add(pagamento)
            
            # Para alguns usuários, criar também inscrições em oficinas
            if random.random() < 0.7:  # 70% de chance
                # Pega oficinas deste evento
                oficinas_evento = [o for o in oficinas if o.evento_id == evento.id]
                
                if oficinas_evento:
                    # Número de oficinas que o usuário se inscreverá
                    num_oficinas = min(random.randint(1, 3), len(oficinas_evento))
                    oficinas_inscritas = random.sample(oficinas_evento, num_oficinas)
                    
                    for oficina in oficinas_inscritas:
                        # Define status de pagamento para oficina
                        if oficina.inscricao_gratuita:
                            status_oficina = 'approved'
                        else:
                            status_oficina = random.choices(
                                STATUS_PAGAMENTO, 
                                weights=[0.2, 0.6, 0.1, 0.1], 
                                k=1
                            )[0]
                        
                        inscricao_oficina = Inscricao(
                            usuario_id=usuario.id,
                            cliente_id=evento.cliente_id,
                            oficina_id=oficina.id,
                            status_pagamento=status_oficina
                        )
                        db.session.add(inscricao_oficina)
                        inscricoes.append(inscricao_oficina)
    
    db.session.commit()
    
    # Após criar inscrições, criar checkins para algumas delas
    criar_checkins(inscricoes, oficinas, eventos)
    
    # Criar feedbacks para algumas oficinas
    criar_feedbacks(inscricoes, oficinas)
    
    return inscricoes

def criar_checkins(inscricoes, oficinas, eventos):
    """Cria registros de checkin para inscrições"""
    # Filtra inscrições com pagamento aprovado
    inscricoes_validas = [i for i in inscricoes if i.status_pagamento == 'approved']
    
    for inscricao in inscricoes_validas:
        # 70% de chance de ter checkin
        if random.random() < 0.7:
            if inscricao.oficina_id:
                # Checkin em oficina
                oficina = next((o for o in oficinas if o.id == inscricao.oficina_id), None)
                if oficina and oficina.dias:
                    # Pega um dia aleatório da oficina
                    dia = random.choice(oficina.dias)
                    
                    # Decide se é checkin na palavra da manhã ou da tarde
                    if random.choice([True, False]):
                        palavra = dia.palavra_chave_manha
                    else:
                        palavra = dia.palavra_chave_tarde
                    
                    checkin = Checkin(
                        usuario_id=inscricao.usuario_id,
                        oficina_id=inscricao.oficina_id,
                        data_hora=dia.data + timedelta(hours=random.randint(0, 8)),
                        palavra_chave=palavra,
                        cliente_id=inscricao.cliente_id
                    )
                    db.session.add(checkin)
            
            elif inscricao.evento_id:
                # Checkin em evento
                evento = next((e for e in eventos if e.id == inscricao.evento_id), None)
                if evento:
                    checkin = Checkin(
                        usuario_id=inscricao.usuario_id,
                        evento_id=inscricao.evento_id,
                        data_hora=evento.data_inicio + timedelta(hours=random.randint(0, 8)),
                        palavra_chave="EVENTO",
                        cliente_id=inscricao.cliente_id
                    )
                    db.session.add(checkin)
    
    db.session.commit()

def criar_feedbacks(inscricoes, oficinas):
    """Cria feedbacks para oficinas"""
    inscricoes_oficinas = [i for i in inscricoes if i.oficina_id and i.status_pagamento == 'approved']
    
    for inscricao in inscricoes_oficinas:
        # 50% de chance de deixar feedback
        if random.random() < 0.5:
            oficina = next((o for o in oficinas if o.id == inscricao.oficina_id), None)
            if oficina:
                # Rating de 1 a 5 estrelas, com tendência para avaliações positivas
                rating = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.1, 0.2, 0.3, 0.35], k=1)[0]
                
                # Comentário baseado na avaliação
                if rating >= 4:
                    comentario = random.choice([
                        f"Excelente oficina! {fake.sentence()}",
                        f"Adorei o conteúdo apresentado. {fake.sentence()}",
                        f"O ministrante {oficina.ministrante_obj.nome} foi muito didático. {fake.sentence()}"
                    ])
                elif rating == 3:
                    comentario = random.choice([
                        f"Oficina boa, mas poderia ser melhor. {fake.sentence()}",
                        f"Conteúdo interessante, mas a didática pode melhorar. {fake.sentence()}"
                    ])
                else:
                    comentario = random.choice([
                        f"Não atendeu às minhas expectativas. {fake.sentence()}",
                        f"Conteúdo muito básico para o que foi proposto. {fake.sentence()}"
                    ])
                
                feedback = Feedback(
                    usuario_id=inscricao.usuario_id,
                    oficina_id=inscricao.oficina_id,
                    rating=rating,
                    comentario=comentario
                )
                db.session.add(feedback)
    
    db.session.commit()


@pytest.fixture
def mock_evento():
    evento = Mock()
    oficina = Mock()
    horario = Mock()
    
    # Configure mocks
    horario.vagas_disponiveis = 20
    horario.id = 1
    oficina.horarios = [horario]
    evento.oficinas = [oficina]
    
    return evento

@pytest.fixture 
def mock_usuarios():
    professor = Mock()
    professor.tipo = 'professor'
    professor.id = 1
    return [professor]

def test_criar_agendamentos_sem_vagas(mock_evento, mock_usuarios):
    # Arrange
    mock_evento.oficinas[0].horarios[0].vagas_disponiveis = 0
    
    # Act
    resultado = criar_agendamentos_visita([mock_evento], mock_usuarios)
    
    # Assert  
    assert len(resultado) == 0

def test_criar_agendamentos_com_vagas(mock_evento, mock_usuarios):
    # Arrange
    random.seed(42) # For reproducible results
    mock_evento.oficinas[0].horarios[0].vagas_disponiveis = 20
    
    # Act
    resultado = criar_agendamentos_visita([mock_evento], mock_usuarios)
    
    # Assert
    assert len(resultado) > 0
    assert resultado[0].quantidade_alunos <= 20

def test_criar_agendamentos_respeita_limite_maximo(mock_evento, mock_usuarios):
    # Arrange
    mock_evento.oficinas[0].horarios[0].vagas_disponiveis = 50
    
    # Act
    resultado = criar_agendamentos_visita([mock_evento], mock_usuarios)
    
    # Assert
    assert all(a.quantidade_alunos <= 30 for a in resultado)

def criar_submissoes(eventos, usuarios, quantidade_por_evento=3):
    """Gera trabalhos submetidos (Submission) ligados a participantes."""
    participantes = [u for u in usuarios if u.tipo in ("participante", "professor")]
    if not participantes:
        return [], []

    submissoes = []
    logs = []

    for evento in eventos:
        for _ in range(quantidade_por_evento):
            autor = random.choice(participantes)
            raw_code = fake.lexify(text="??????")
            code_hash = bcrypt.hashpw(raw_code.encode(), bcrypt.gensalt()).decode()
            sub = Submission(
                title=fake.sentence(nb_words=6),
                abstract=fake.paragraph(),
                content=fake.paragraph(nb_sentences=3),
                file_path=f"submissoes/{uuid.uuid4()}.pdf",
                code_hash=code_hash,
                status=random.choice(["submitted", "in_review", "accepted", "rejected"]),
                area_id=evento.id,
                author_id=autor.id,
            )
            db.session.add(sub)
            db.session.flush()

            log = AuditLog(user_id=autor.id, submission_id=sub.id, event_type="submission")
            db.session.add(log)

            submissoes.append(sub)
            logs.append(log)

    db.session.commit()
    return submissoes, logs


def criar_reviews_assignments(submissoes, usuarios):
    """Cria tarefas de revisão e registros de Review para as submissões."""
    revisores = [u for u in usuarios if u.tipo in ("professor", "cliente", "superadmin")]
    if not revisores:
        return [], [], []

    reviews = []
    assignments = []
    logs = []

    for sub in submissoes:
        selecionados = random.sample(revisores, min(2, len(revisores)))
        for reviewer in selecionados:
            assignment = Assignment(
                submission_id=sub.id,
                reviewer_id=reviewer.id,
                deadline=datetime.utcnow() + timedelta(days=random.randint(5, 15)),
                completed=True,
            )
            db.session.add(assignment)
            assignments.append(assignment)

            review = Review(
                submission_id=sub.id,
                reviewer_id=reviewer.id,
                locator=str(uuid.uuid4()),
                access_code=str(random.randint(100000, 999999)),
                blind_type=random.choice(["single", "double"]),
                scores={"originalidade": random.randint(1, 5), "clareza": random.randint(1, 5)},
                note=random.randint(0, 10),
                comments=fake.paragraph(),
                decision=random.choice(["accept", "minor", "major", "reject"]),
            )
            db.session.add(review)
            reviews.append(review)

            log = AuditLog(user_id=reviewer.id, submission_id=sub.id, event_type="review")
            db.session.add(log)
            logs.append(log)

    db.session.commit()
    return reviews, assignments, logs


def criar_binarios(submissoes, quantidade=3):
    """Gera alguns ArquivoBinario ligados às submissões."""
    arquivos = []
    alvos = random.sample(submissoes, min(len(submissoes), quantidade)) if submissoes else []
    for sub in alvos:
        conteudo = fake.text().encode()
        arq = ArquivoBinario(nome=f"sub_{sub.id}.txt", conteudo=conteudo, mimetype="text/plain")
        db.session.add(arq)
        db.session.flush()
        sub.file_path = f"binario_{arq.id}"  # referência simples
        arquivos.append(arq)
    db.session.commit()
    return arquivos

def popular_banco():
    """Função principal para popular o banco de dados"""
    print("Iniciando população do banco de dados...")
    
    # Limpa tabelas existentes (opcional - tenha cuidado em produção!)
    # db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    # Adicione comandos para limpar tabelas se necessário
    # db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    
    print("Criando clientes...")
    clientes = criar_clientes(5)
    
    print("Criando eventos...")
    eventos = criar_eventos(clientes, 10)
    
    print("Criando ministrantes...")
    ministrantes = criar_ministrantes(clientes, 20)
    
    print("Criando oficinas...")
    oficinas = criar_oficinas(eventos, ministrantes, 10)
    
    print("Criando usuários...")
    usuarios = criar_usuarios(clientes, 200)

    print("Criando inscrições...")
    inscricoes = criar_inscricoes(usuarios, eventos, oficinas)

    print("Criando submissões...")
    submissoes, logs_sub = criar_submissoes(eventos, usuarios)

    print("Criando reviews e assignments...")
    reviews, assignments, logs_rev = criar_reviews_assignments(submissoes, usuarios)

    print("Criando arquivos binários...")
    arquivos = criar_binarios(submissoes)

    audit_logs = logs_sub + logs_rev

    print("Criando agendamentos de visita...")
    agendamentos = criar_agendamentos_visita(eventos, usuarios)

    print("Banco de dados populado com sucesso!")
    print("Foram criados:")
    print(f"- {len(clientes)} clientes")
    print(f"- {len(eventos)} eventos")
    print(f"- {len(ministrantes)} ministrantes")
    print(f"- {len(oficinas)} oficinas")
    print(f"- {len(usuarios)} usuários")
    print(f"- {len(inscricoes)} inscrições")
    print(f"- {len(submissoes)} submissões")
    print(f"- {len(reviews)} reviews")
    print(f"- {len(assignments)} assignments")
    print(f"- {len(arquivos)} arquivos binários")
    print(f"- {len(agendamentos)} agendamentos de visita")
    
    return {
        'clientes': clientes,
        'eventos': eventos,
        'ministrantes': ministrantes,
        'oficinas': oficinas,
        'usuarios': usuarios,
        'inscricoes': inscricoes,
        'submissoes': submissoes,
        'reviews': reviews,
        'assignments': assignments,
        'arquivos': arquivos,
        'audit_logs': audit_logs,
        'agendamentos': agendamentos
    }

# Se este script for executado diretamente, popula o banco
if __name__ == "__main__":
    # Aqui você deve importar seu app Flask e contexto
    # from app import app, db
    # with app.app_context():
    #     popular_banco()
    
    # Se você estiver usando este script fora do aplicativo Flask, configure o contexto
    print("Para executar este script, você deve importá-lo em seu aplicativo Flask")
    print("e executá-lo dentro de um contexto de aplicativo.")
    print("Exemplo:")
    print("```")
    print("from app import app, db")
    print("from populate_script import popular_banco")
    print("with app.app_context():")
    print("    popular_banco()")
    print("```")
