
/* global window */
(function () {
  const container = document.getElementById('configSubmissao');
  if (!container) return;

  // Global URL for other scripts
  if (!window.URL_CONFIG_CLIENTE_ATUAL) {
    window.URL_CONFIG_CLIENTE_ATUAL = container.dataset.urlConfigClienteAtual || '';
  }

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

  function attachOnce(el, event, handler) {
    if (!el) return;
    const key = `listener_${event}`;
    if (el.dataset[key]) return;
    el.dataset[key] = 'true';
    el.addEventListener(event, handler);
  }

  const REVISAO_CONFIGS = JSON.parse(container.dataset.revisaoConfigs || '{}');
  const formRevisao = document.getElementById('formRevisaoConfig');
  const selectEventoRevisao = document.getElementById('selectEventoRevisao');
  const inputNumeroRevisores = document.getElementById('inputNumeroRevisores');
  const inputPrazoRevisao = document.getElementById('inputPrazoRevisao');
  const selectModeloBlind = document.getElementById('selectModeloBlind');

  function carregarConfig(id) {
    const cfg = REVISAO_CONFIGS[id] || {};
    if (inputNumeroRevisores) inputNumeroRevisores.value = cfg.numero_revisores || 2;
    if (inputPrazoRevisao) inputPrazoRevisao.value = cfg.prazo_revisao ? cfg.prazo_revisao.split('T')[0] : '';
    if (selectModeloBlind) selectModeloBlind.value = cfg.modelo_blind || 'single';
  }

  if (selectEventoRevisao) {
    carregarConfig(selectEventoRevisao.value);
    attachOnce(selectEventoRevisao, 'change', () => carregarConfig(selectEventoRevisao.value));
  }

  attachOnce(formRevisao, 'submit', async (e) => {
    e.preventDefault();
    const eventoId = selectEventoRevisao.value;
    const payload = {
      numero_revisores: parseInt(inputNumeroRevisores.value, 10),
      modelo_blind: selectModeloBlind.value,
    };
    if (inputPrazoRevisao.value) {
      payload.prazo_revisao = inputPrazoRevisao.value;
    }
    const resp = await fetch(`/revisao_config/${eventoId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify(payload),
    });
    if (resp.ok) {
      REVISAO_CONFIGS[eventoId] = payload;
      alert('Configuração de revisão atualizada');
    } else {
      alert('Erro ao salvar configuração');
    }
  });

  document.querySelectorAll('.gerar-codigos').forEach((btn) => {
    attachOnce(btn, 'click', () => {
      const loc = btn.dataset.locator;
      fetch(`/submissions/${loc}/codes`)
        .then((r) => r.json())
        .then((data) => {
          if (data.reviews) {
            alert(data.reviews.map((r) => r.access_code).join('\n'));
          }
        });
    });
  });

  const minRev = parseInt(container.dataset.minRev || '1', 10);
  const maxRev = parseInt(container.dataset.maxRev || '2', 10);

  attachOnce(document.getElementById('assignManual'), 'click', () => {
    const subId = document.getElementById('submissionSelect').value;
    const selected = Array.from(
      document.getElementById('reviewerSelect').selectedOptions,
    ).map((o) => o.value);
    if (selected.length < minRev || selected.length > maxRev) {
      alert(`Selecione entre ${minRev} e ${maxRev} revisores.`);
      return;
    }
    const payload = {};
    payload[subId] = selected;
    fetch('/assign_reviews', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          alert('Revisores atribuídos com sucesso');
          location.reload();
        } else {
          alert('Falha ao atribuir revisores');
        }
      });
  });

  attachOnce(document.getElementById('assignAutomatic'), 'click', () => {
    fetch('/assign_by_filters', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ filters: {} }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          alert('Sorteio realizado');
          location.reload();
        } else {
          alert(data.message || 'Falha no sorteio');
        }
      });
  });

  attachOnce(document.getElementById('autoArea'), 'click', () => {
    const eventoId = document.getElementById('eventoId').value;
    if (!eventoId) {
      alert('Informe o ID do evento');
      return;
    }
    fetch(`/auto_assign/${eventoId}`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) {
          alert('Atribuições criadas');
          location.reload();
        } else {
          alert(data.message || 'Erro na atribuição automática');
        }
      });
  });
})();
