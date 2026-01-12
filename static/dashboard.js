document.addEventListener('DOMContentLoaded', () => {
    // --- Elementos do DOM ---
    const searchInput = document.getElementById('search-input');
    const sortSelect = document.getElementById('sort-select');
    const versionFilterSelect = document.getElementById('version-filter-select');
    const cardGrid = document.getElementById('card-grid');
    const themeToggle = document.getElementById('theme-toggle');
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const updateSelectedBtn = document.getElementById('update-selected-btn');
    const clientCheckboxes = document.querySelectorAll('.client-select-checkbox');

    // --- NOVO: LÓGICA DO MODAL DE VISUALIZAÇÃO DE FEEDBACK ---
    const viewFeedbackModal = document.getElementById('view-feedback-modal');
    const viewFeedbackTitle = document.getElementById('view-feedback-modal-title');
    const viewFeedbackListContainer = document.getElementById('view-feedback-list-container');
    const viewFeedbackLoader = document.getElementById('view-feedback-loader');

    const openViewFeedbackModal = async (maquina) => {
        const nickname = localStorage.getItem(`nickname_${maquina}`) || maquina;
        viewFeedbackTitle.textContent = `Histórico de Feedback de ${nickname}`;
        
        viewFeedbackListContainer.innerHTML = ''; // Limpa a lista
        viewFeedbackLoader.style.display = 'block'; // Mostra o loader
        viewFeedbackModal.style.display = 'flex';

        try {
            const response = await fetch(`/api/feedback/history/${maquina}`);
            if (!response.ok) throw new Error('Falha ao buscar histórico.');
            
            const history = await response.json();
            viewFeedbackLoader.style.display = 'none';

            if (history.length === 0) {
                viewFeedbackListContainer.innerHTML = '<p class="text-center text-gray-500 p-4">Nenhum feedback encontrado para este cliente.</p>';
                return;
            }

            // Marca o feedback mais recente como visto no localStorage
            const latestTimestamp = history[0].timestamp;
            localStorage.setItem(`lastSeenFeedback_${maquina}`, latestTimestamp);

            history.forEach(item => {
                // Renderiza as estrelas
                let starsHTML = '';
                for (let i = 0; i < 5; i++) {
                    starsHTML += `<i class="${i < item.rating ? 'fas fa-star text-yellow-400' : 'far fa-star text-gray-400'}"></i>`;
                }

                // Renderiza os placeholders
                let placeholdersHTML = '';
                if (item.placeholders && item.placeholders.length > 0) {
                    placeholdersHTML = item.placeholders.map(text => 
                        `<span class="text-xs font-semibold bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 px-2 py-1 rounded-full">${text}</span>`
                    ).join('');
                }
                
                const formattedDate = new Date(item.timestamp).toLocaleString('pt-BR', {
                    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
                });

                // Cria o card para este item do histórico
                const feedbackItemHTML = `
                    <div class="border-b dark:border-gray-700 pb-3 mb-3 last:border-b-0 last:mb-0">
                        <div class="flex justify-between items-start mb-2">
                            <div class="flex text-xl">${starsHTML}</div>
                            <div class="text-right">
                                <span class="text-xs text-gray-500 dark:text-gray-400">${formattedDate}</span>
                                <span class="text-xs font-semibold text-gray-600 dark:text-gray-300 block">por: ${item.user}</span>
                            </div>
                        </div>
                        ${placeholdersHTML ? `<div class="flex flex-wrap gap-2 my-2">${placeholdersHTML}</div>` : ''}
                        <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">${item.comment || '<i>Nenhum comentário adicional.</i>'}</p>
                    </div>
                `;
                viewFeedbackListContainer.innerHTML += feedbackItemHTML;
            });

        } catch (error) {
            viewFeedbackLoader.style.display = 'none';
            viewFeedbackListContainer.innerHTML = `<p class="text-center text-red-500 p-4">Erro ao carregar o histórico: ${error.message}</p>`;
        }
    };

    const closeViewFeedbackModal = () => {
        viewFeedbackModal.style.display = 'none';
    };

    document.getElementById('view-feedback-close-btn').addEventListener('click', closeViewFeedbackModal);
    document.getElementById('view-feedback-ok-btn').addEventListener('click', closeViewFeedbackModal);
    viewFeedbackModal.addEventListener('click', (e) => {
        if (e.target === viewFeedbackModal) closeViewFeedbackModal();
    });

    // --- LÓGICA DE FILTRO E ORDENAÇÃO ---
    const applyFiltersAndSort = () => {
        const searchTerm = searchInput.value.toLowerCase();
        const sortValue = sortSelect.value;
        const selectedVersion = versionFilterSelect.value;
        const cards = Array.from(cardGrid.querySelectorAll('.client-card'));

        cards.forEach(card => {
            const maquina = card.dataset.maquina.toLowerCase();
            const version = card.dataset.version;
            const nickname = (card.querySelector('.maquina-nome-display').textContent || '').toLowerCase();

            const matchesSearch = maquina.includes(searchTerm) || nickname.includes(searchTerm);
            const matchesVersion = (selectedVersion === 'all') || (version === selectedVersion);
            
            const shouldShow = matchesSearch && matchesVersion;
            card.style.display = shouldShow ? 'flex' : 'none';
        });

        const sortedCards = cards.filter(card => card.style.display !== 'none').sort((a, b) => {
            if (sortValue === 'name-asc') {
                const nameA = a.querySelector('.maquina-nome-display').textContent.trim();
                const nameB = b.querySelector('.maquina-nome-display').textContent.trim();
                return nameA.localeCompare(nameB);
            }
            if (sortValue === 'status') return a.dataset.statusOrder - b.dataset.statusOrder;
            return 0;
        });
        
        sortedCards.forEach(card => cardGrid.appendChild(card));
    };
    
    // --- LÓGICA DE APELIDOS E COMENTÁRIOS (LocalStorage) ---
    const loadAndApplyLocalData = () => {
        document.querySelectorAll('.client-card').forEach(card => {
            const maquina = card.dataset.maquina;
            
            // Carregar apelidos
            const savedNickname = localStorage.getItem(`nickname_${maquina}`);
            if (savedNickname) {
                card.querySelector('.maquina-nome-display').textContent = savedNickname;
            }

            // Carregar e indicar comentários
            const savedComment = localStorage.getItem(`comment_${maquina}`);
            const commentBtn = card.querySelector('.comment-btn');
            if (savedComment && commentBtn) {
                commentBtn.classList.add('has-comment');
                commentBtn.title = `Editar Anotações: "${savedComment.substring(0, 30)}..."`;
            }
        });
    };

    const handleRename = (button) => {
        const card = button.closest('.client-card');
        const nameDisplay = card.querySelector('.maquina-nome-display');
        const maquinaID = card.dataset.maquina; // O ID único (hostname)
        const currentDisplayName = nameDisplay.textContent;

        // Cria o input
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'nickname-input';
        input.value = currentDisplayName;
        
        // Substitui o H2 pelo Input
        nameDisplay.replaceWith(input);
        input.focus();
        input.select();

        const saveNickname = async () => {
            const newName = input.value.trim();
            
            // Trava o input enquanto salva
            input.disabled = true;
            input.style.cursor = 'wait';

            try {
                const response = await fetch('/api/renomear', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        maquina: maquinaID, 
                        novo_nome: newName 
                    })
                });

                if (!response.ok) throw new Error('Falha ao salvar no servidor');

                // Atualiza visualmente
                nameDisplay.textContent = newName || maquinaID; // Se vazio, volta algo (pode ajustar)
                
                // Sucesso: troca o input de volta pelo texto
                input.replaceWith(nameDisplay);
                
                // Re-aplica filtros (para reordenar se estiver por nome A-Z)
                applyFiltersAndSort();

            } catch (error) {
                alert('Erro ao salvar apelido: ' + error.message);
                // Em caso de erro, restaura o antigo
                nameDisplay.textContent = currentDisplayName;
                input.replaceWith(nameDisplay);
            }
        };

        // Salvar ao perder foco ou dar Enter
        input.addEventListener('blur', saveNickname);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                input.blur(); // Dispara o evento blur acima
            }
            if (e.key === 'Escape') {
                // Cancela
                nameDisplay.textContent = currentDisplayName;
                input.replaceWith(nameDisplay);
            }
        });
    };
    
    const commentModal = document.getElementById('comment-modal');
    const modalTitle = document.getElementById('modal-title');
    const commentTextarea = document.getElementById('comment-textarea');
    let currentEditingMaquina = null;

    const openCommentModal = (maquina) => {
        currentEditingMaquina = maquina;
        const nickname = localStorage.getItem(`nickname_${maquina}`) || maquina;
        modalTitle.textContent = `Anotações para ${nickname}`;
        commentTextarea.value = localStorage.getItem(`comment_${maquina}`) || '';
        commentModal.style.display = 'flex';
        commentTextarea.focus();
    };

    const closeCommentModal = () => {
        commentModal.style.display = 'none';
        currentEditingMaquina = null;
    };

    // --- LÓGICA DE ATUALIZAÇÃO REMOTA (COMPLETA) ---
    let latestVersion = null;

    const compareVersions = (v1, v2) => {
        if (!v1 || !v2 || v1 === 'N/A' || v2 === 'N/A') return 0;
        const parts1 = v1.split('.').map(Number);
        const parts2 = v2.split('.').map(Number);
        const len = Math.max(parts1.length, parts2.length);
        for (let i = 0; i < len; i++) {
            const p1 = parts1[i] || 0;
            const p2 = parts2[i] || 0;
            if (p1 > p2) return 1;
            if (p1 < p2) return -1;
        }
        return 0;
    };

    const checkAllClientsForUpdates = async () => {
        try {
            const response = await fetch('/api/update/check_latest_version');
            if (!response.ok) return;
            const data = await response.json();
            latestVersion = data.latest_version;

            // --- ADICIONE ESTA PARTE AQUI ---
            const badgeNumber = document.getElementById('global-version-number');
            if (badgeNumber) {
                badgeNumber.textContent = latestVersion; // Atualiza o texto do badge
            }
            // --------------------------------

            document.querySelectorAll('.client-card').forEach(card => {
                // ... (seu código existente de comparação de versão) ...
            });
        } catch (error) {
            console.error("Erro ao verificar versão mais recente:", error);
            // Opcional: mostrar erro no badge
            const badgeNumber = document.getElementById('global-version-number');
            if(badgeNumber) badgeNumber.textContent = "Erro";
        }
    };

    const triggerClientUpdate = async (maquina, button) => {
        if (!confirm(`Tem certeza que deseja iniciar a atualização para o cliente ${maquina}?`)) return;

        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;

        try {
            const response = await fetch(`/api/update/${maquina}/trigger`, { method: 'POST' });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Erro do servidor');
            alert(`Sucesso para ${maquina}: ${data.message}`);
        } catch (error) {
            alert(`Falha para ${maquina}: ${error.message}`);
        } finally {
            button.innerHTML = originalHTML;
            checkAllClientsForUpdates();
        }
    };

    // --- LÓGICA DE AÇÕES EM MASSA (COMPLETA) ---
    const updateBulkButtonState = () => {
        if (!updateSelectedBtn || !clientCheckboxes) return;
        const anySelected = Array.from(clientCheckboxes).some(cb => cb.checked);
        updateSelectedBtn.disabled = !anySelected;
    };

    if (updateSelectedBtn) {
        updateSelectedBtn.addEventListener('click', async () => {
            const selectedMaquinas = Array.from(clientCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.dataset.maquina);
            
            if (selectedMaquinas.length === 0) return;
            if (!confirm(`Você está prestes a iniciar a atualização para ${selectedMaquinas.length} clientes. Continuar?`)) return;

            const originalText = updateSelectedBtn.innerHTML;
            updateSelectedBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
            updateSelectedBtn.disabled = true;

            const updatePromises = selectedMaquinas.map(maquina => 
                fetch(`/api/update/${maquina}/trigger`, { method: 'POST' })
                .then(res => res.json().then(data => ({ maquina, success: res.ok, data })))
                .catch(err => ({ maquina, success: false, data: { message: err.message } }))
            );

            const results = await Promise.all(updatePromises);
            
            let successMessages = 'Comandos enviados com sucesso para:\n';
            let errorMessages = 'Falha ao enviar comando para:\n';
            let successCount = 0;
            let errorCount = 0;

            results.forEach(result => {
                if (result.success) {
                    successCount++;
                    successMessages += `- ${result.maquina}: ${result.data.message}\n`;
                } else {
                    errorCount++;
                    errorMessages += `- ${result.maquina}: ${result.data.message}\n`;
                }
            });

            let finalReport = '';
            if (successCount > 0) finalReport += successMessages;
            if (errorCount > 0) finalReport += `\n${errorMessages}`;
            alert(finalReport);
            
            updateSelectedBtn.innerHTML = originalText;
            updateBulkButtonState();
            selectAllCheckbox.checked = false;
            clientCheckboxes.forEach(cb => cb.checked = false);
        });
    }

    // --- CONECTIVIDADE E SERVIÇOS (REFATORADO) ---
    const AGENT_PORT = 5002;

    const checkIpConnectivity = async (card) => {
        const ip = card.dataset.ip;
        const vpnIcon = card.querySelector('.vpn-status-icon');
        
        // Se não tiver IP ou ícone, aborta
        if (!ip || ip === 'N/A' || !vpnIcon) {
            if (vpnIcon) vpnIcon.style.display = 'none';
            return;
        }

        // Estado Inicial: Verificando (Spinner Azul)
        vpnIcon.style.display = 'inline-block';
        vpnIcon.className = 'fas fa-plug vpn-status-icon checking fa-spin'; // Adicionado fa-spin para animação
        vpnIcon.style.color = 'var(--color-warning)'; // Cor amarela/azul de loading
        vpnIcon.title = `Tentando conectar em ${ip}:${AGENT_PORT}...`;

        try {
            const controller = new AbortController();
            // Timeout reduzido para 2 segundos para falhar mais rápido se não responder
            const timeoutId = setTimeout(() => controller.abort(), 2000);

            // Tenta bater na porta 5002 do cliente
            await fetch(`http://${ip}:${AGENT_PORT}/`, { 
                method: 'HEAD', 
                mode: 'no-cors', 
                signal: controller.signal 
            });
            
            clearTimeout(timeoutId);

            // SUCESSO: Conectado (Plug Verde)
            vpnIcon.className = 'fas fa-plug vpn-status-icon connected';
            vpnIcon.style.color = 'var(--color-online)'; // Verde
            vpnIcon.classList.remove('fa-spin');
            vpnIcon.title = `Agente online em ${ip}. Conexão local OK.`;

        } catch (error) {
            // ERRO: Falha na conexão (Plug Vermelho)
            // O erro ERR_CONNECTION_REFUSED cairá aqui
            vpnIcon.className = 'fas fa-plug vpn-status-icon disconnected';
            vpnIcon.style.color = 'var(--color-offline)'; // Vermelho
            vpnIcon.classList.remove('fa-spin');
            
            // Mensagem de erro específica no tooltip
            if (error.name === 'AbortError') {
                vpnIcon.title = `Timeout: O agente em ${ip} demorou muito para responder.`;
            } else {
                vpnIcon.title = `Conexão recusada em ${ip}. O Agente (porta ${AGENT_PORT}) parece estar parado ou bloqueado.`;
            }
        }
    };

    const checkHttpsConnectivity = async (card) => {
        const domain = card.dataset.domain;
        const icon = card.querySelector('.https-check-icon');
        const text = card.querySelector('.https-status-text');
        
        // Se não houver esses elementos visuais, aborta para evitar erros no console
        if (!icon || !text) return;

        // Se o domínio for "None", vazio ou indefinido (correção do hífen)
        if (!domain || domain === 'None' || domain.trim() === "") {
            icon.style.display = 'none'; // Esconde a bolinha girando
            text.textContent = "-";      // Mostra que não há site configurado
            return;
        }

        try {
            // Define um limite de tempo (timeout) de 5 segundos para não ficar pendurado
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            // Faz a requisição "HEAD" (só cabeçalho, leve) em modo no-cors (aceita resposta opaca)
            await fetch(domain, { 
                method: 'HEAD', 
                mode: 'no-cors', 
                signal: controller.signal 
            });
            
            clearTimeout(timeoutId);

            // SUCESSO
            icon.className = 'fas fa-check-circle';
            icon.style.color = 'var(--color-online)'; // Verde
            icon.classList.remove('fa-spin'); // Para de girar
            icon.style.display = 'inline-block';
            icon.title = 'Site acessível';
            
            text.textContent = 'Online';
            text.style.color = 'var(--color-online)';

        } catch (error) {
            // ERRO (Site fora do ar, DNS inválido ou Timeout)
            icon.className = 'fas fa-exclamation-triangle';
            icon.style.color = 'var(--color-no-response)'; // Laranja/Vermelho
            icon.classList.remove('fa-spin');
            icon.style.display = 'inline-block';
            
            // Diferencia Timeout de outros erros
            if (error.name === 'AbortError') {
                icon.title = 'Demorou muito para responder (Timeout)';
                text.textContent = 'Lento/Off';
            } else {
                icon.title = 'Não foi possível conectar ao site';
                text.textContent = 'Erro';
            }
            text.style.color = 'var(--color-no-response)';
        }
    };

    const runAllConnectivityChecks = () => {
        document.querySelectorAll('.client-card').forEach(card => {
            checkIpConnectivity(card);
            checkHttpsConnectivity(card); // Adicionado ao ciclo
        });
    };
    
    // --- NOVA FUNÇÃO DE CONTROLE DE SERVIÇO VIA BANCO DE DADOS ---
    const enviarComandoRemoto = async (maquina, comando, button) => {
        const originalHTML = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            // Chama a nova rota do backend que insere no banco
            const response = await fetch('/api/comando_remoto', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ maquina, comando })
            });
            
            const result = await response.json();

            if (response.ok && result.status === 'success') {
                // Notifica o usuário que a ordem foi enfileirada
                alert(`Comando ${comando} enviado para ${maquina}. Aguarde o próximo ciclo do agente (até 60s).`);
                
                // Atualização visual otimista do botão de Pause/Resume
                if (comando === 'PAUSE') {
                    button.dataset.action = 'start'; // Próxima ação será 'start' (RESUME)
                    button.title = "Retomar Serviço (Resume)";
                    // O ícone será atualizado no bloco finally
                } else if (comando === 'RESUME') {
                    button.dataset.action = 'stop'; // Próxima ação será 'stop' (PAUSE)
                    button.title = "Pausar Serviço (Pause)";
                }
            } else {
                alert(`Erro ao processar comando: ${result.message}`);
            }
        } catch (error) {
            console.error('Erro ao enviar comando remoto:', error);
            alert(`Falha de comunicação com o servidor: ${error.message}`);
        } finally {
            button.disabled = false;
            
            // Restaura ou atualiza o ícone
            if (comando === 'RESTART') {
                button.innerHTML = originalHTML;
            } else {
                // Se foi Pause/Resume, atualiza o ícone baseado no novo dataset.action
                const isNowPaused = button.dataset.action === 'start'; // Se a próxima ação é start, é pq está pausado
                const iconClass = isNowPaused ? 'fa-play' : 'fa-pause';
                button.innerHTML = `<i class="fas ${iconClass}"></i>`;
            }
        }
    };

    const handleDelete = (maquina, card) => {
        if (confirm(`Tem certeza que deseja excluir TODOS os registros do cliente "${maquina}"? Esta ação não pode ser desfeita.`)) {
            fetch(`/api/cliente/${maquina}/delete`, { method: 'POST' })
            .then(response => response.json().then(data => ({ ok: response.ok, data })))
            .then(({ ok, data }) => {
                if (ok) {
                    alert(data.message);
                    card.remove(); 
                } else {
                    throw new Error(data.message || 'Erro desconhecido');
                }
            })
            .catch(error => {
                console.error('Erro ao excluir cliente:', error);
                alert(`Falha ao excluir cliente: ${error.message}`);
            });
        }
    };
    
    // --- LÓGICA DO TEMA (MODO ESCURO) ---
    const applyTheme = (isDark) => {
        document.body.classList.toggle('dark-mode', isDark);
        if (themeToggle) themeToggle.checked = isDark;
    };

    // --- ATUALIZAÇÃO DO TÍTULO DA PÁGINA COM ALERTAS ---
    const updatePageTitle = () => {
        if (typeof DASHBOARD_DATA !== 'undefined') {
            const { total_online, total_clientes } = DASHBOARD_DATA;
            if (total_online < total_clientes) {
                document.title = `(${total_clientes - total_online}) Alerta! - Painel VYA Manager`;
            } else {
                document.title = 'Painel de Monitoramento - VYA Manager';
            }
        }
    };

    // --- REGISTRO DE EVENTOS E INICIALIZAÇÃO ---

    // Event listeners para filtros e ordenação
    [searchInput, sortSelect, versionFilterSelect].forEach(el => {
        if (el) el.addEventListener('input', applyFiltersAndSort);
    });

    // Event listeners para o seletor de tema
    if (themeToggle) {
        themeToggle.addEventListener('change', () => {
            localStorage.setItem('darkMode', themeToggle.checked);
            applyTheme(themeToggle.checked);
        });
    }

    // Event listeners para o modal de comentários
    document.getElementById('modal-save-btn').addEventListener('click', () => {
        if (!currentEditingMaquina) return;
        const comment = commentTextarea.value.trim();
        const card = document.querySelector(`.client-card[data-maquina="${currentEditingMaquina}"]`);
        const commentBtn = card.querySelector('.comment-btn');

        if (comment) {
            localStorage.setItem(`comment_${currentEditingMaquina}`, comment);
            commentBtn.classList.add('has-comment');
            commentBtn.title = `Editar Anotações: "${comment.substring(0, 30)}..."`;
        } else {
            localStorage.removeItem(`comment_${currentEditingMaquina}`);
            commentBtn.classList.remove('has-comment');
            commentBtn.title = 'Adicionar Anotações';
        }
        closeCommentModal();
    });
    document.getElementById('modal-cancel-btn').addEventListener('click', closeCommentModal);
    document.getElementById('modal-close-btn').addEventListener('click', closeCommentModal);
    commentModal.addEventListener('click', (e) => {
        if (e.target === commentModal) closeCommentModal();
    });

    // Event listeners para seleção em massa
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', () => {
            clientCheckboxes.forEach(cb => {
                if (cb.closest('.client-card').style.display !== 'none') {
                    cb.checked = selectAllCheckbox.checked;
                }
            });
            updateBulkButtonState();
        });
    }
    if (clientCheckboxes) {
        clientCheckboxes.forEach(cb => cb.addEventListener('change', updateBulkButtonState));
    }

    // Delegação de eventos para os cards
    if (cardGrid) {
        cardGrid.addEventListener('click', (e) => {
            const card = e.target.closest('.client-card');
            if (!card) return;

            const maquina = card.dataset.maquina;
            const target = e.target;
            const actionButton = target.closest('.action-btn');

            // Ignora checkbox
            if (target.closest('.client-select-checkbox')) return;
            
            e.stopPropagation();

            if (actionButton) {
                if (actionButton.classList.contains('rename-btn')) handleRename(actionButton);
                else if (actionButton.classList.contains('comment-btn')) openCommentModal(maquina);
                else if (actionButton.classList.contains('feedback-notification-btn')) {
                    openViewFeedbackModal(maquina);
                    actionButton.style.display = 'none';
                }
                else if (actionButton.classList.contains('view-feedback-history-btn')) {
                    openViewFeedbackModal(maquina);
                }
                else if (actionButton.classList.contains('history-btn')) window.location.href = `/historico/${maquina}`
                else if (actionButton.classList.contains('delete-btn')) handleDelete(maquina, card);
                else if (actionButton.classList.contains('update-trigger-btn')) triggerClientUpdate(maquina, actionButton);
                
                // --- Lógica Refatorada para Controle de Serviço ---
                else if (actionButton.classList.contains('service-btn')) {
                const action = actionButton.dataset.action; 
                
                if (action === 'stop') { 
                    // Lógica de PAUSA (já implementada)
                    if (confirm(`Deseja PAUSAR o serviço em ${maquina}?`)) {
                        enviarComandoRemoto(maquina, 'PAUSE', actionButton);
                    }
                } 
                // --- LÓGICA DE RESUME AQUI ---
                else if (action === 'start') { 
                    // Ícone de Play está visível -> Usuário quer Retomar
                    if (confirm(`Deseja RETOMAR (RESUME) o serviço em ${maquina}?`)) {
                        // Envia 'RESUME' para o banco. O Watchdog lerá isso e sairá do loop de pausa.
                        enviarComandoRemoto(maquina, 'RESUME', actionButton);
                    }
                }

                else if (action === 'restart') {
                    // REINICIAR
                    if (confirm(`Deseja REINICIAR o serviço em ${maquina}? O processo será encerrado e iniciado novamente.`)) {
                        enviarComandoRemoto(maquina, 'RESTART', actionButton);
                    }
                }
                // -----------------------------
            }
            } else {
                // --- MUDANÇA AQUI: Lógica de redirecionamento ao clicar no corpo do card ---
                const domain = card.dataset.domain;
                const ip = card.dataset.ip;

                if (domain && domain.trim() !== "") {
                    // Prioridade: Abrir link HTTPS registrado
                    window.open(domain, '_blank');
                } else if (ip && ip !== 'N/A') {
                    // Fallback: Abrir IP direto porta 8000
                    window.open(`http://${ip}:8000`, '_blank');
                }
            }
        });
    }
    let lastFeedbackCheckTimestamp = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

    const showFeedbackNotification = (maquina, feedback) => {
        const card = document.querySelector(`.client-card[data-maquina="${maquina}"]`);
        if (!card) return;

        const notificationBtn = card.querySelector('.feedback-notification-btn');
        if (!notificationBtn) return;

        // Pega o último feedback visto pelo usuário do localStorage
        const lastSeenTimestamp = localStorage.getItem(`lastSeenFeedback_${maquina}`);
        const newFeedbackTimestamp = feedback.timestamp;

        // Só mostra a notificação se o feedback for mais novo do que o último visto
        if (!lastSeenTimestamp || newFeedbackTimestamp > lastSeenTimestamp) {
            notificationBtn.title = `Novo feedback recebido! Clique para ver o histórico.`;
            notificationBtn.style.display = 'flex';
        }
    };

    const checkForFeedback = async () => {
        const visibleCards = document.querySelectorAll('.client-card');
        const clientNames = Array.from(visibleCards).map(card => card.dataset.maquina);

        if (clientNames.length === 0) return;
        
        try {
            const response = await fetch('/api/feedback/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    clients: clientNames,
                    last_check: lastFeedbackCheckTimestamp
                })
            });
            
            if (!response.ok) return;

            const newFeedbacks = await response.json();

            // Atualiza o timestamp para a próxima verificação
            lastFeedbackCheckTimestamp = new Date().toISOString();

            for (const maquina in newFeedbacks) {
                if (newFeedbacks.hasOwnProperty(maquina)) {
                    showFeedbackNotification(maquina, newFeedbacks[maquina]);
                }
            }
        } catch (error) {
            console.error("Erro ao verificar por feedback:", error);
        }
    };

    // Inicia o ciclo de verificação
    checkForFeedback(); // Verifica uma vez ao carregar a página
    setInterval(checkForFeedback, 45000); // Verifica a cada 45 segundos
    
    // --- FUNÇÕES DE INICIALIZAÇÃO ---
    applyTheme(localStorage.getItem('darkMode') === 'true');
    loadAndApplyLocalData();
    applyFiltersAndSort();
    updatePageTitle();
    checkAllClientsForUpdates();
    
    // Inicia verificações
    runAllConnectivityChecks();
    setInterval(runAllConnectivityChecks, 30000); 
});