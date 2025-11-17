document.addEventListener('DOMContentLoaded', () => {

    // ▼▼▼ APIベースURLを関数の外に定義 ▼▼▼
    const API_BASE_URL = 'http://localhost:8080/api/v1';

    // --- 要素の取得 ---
    const projectGrid = document.getElementById('project-grid');
    const resultCountSpan = document.getElementById('result-count');
    const searchInput = document.getElementById('search-input');
    const skillFilterContainer = document.querySelector('.skill-filter');

    // 詳細モーダル要素をDOMから取得
    const detailModal = document.getElementById('project-detail-modal');
    const detailCloseBtn = document.getElementById('detail-modal-close-btn');
    const applyForm = document.getElementById('apply-to-project-form');
    const applyProjectIdInput = document.getElementById('apply-project-id');
    const applyFormError = document.getElementById('apply-form-error');

    // --- ユーティリティ関数 ---

    const escapeHTML = (str) => {
        if (!str) return '';
        return str.replace(/[&<>"']/g, (match) => {
            const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
            return map[match];
        });
    };

    // --- API呼び出し関数 ---

    /**
     * プロジェクト詳細をAPIから取得する
     */
    async function fetchProjectDetails(projectId) {
        const token = localStorage.getItem('access_token');
        const endpoint = `${API_BASE_URL}/projects/${projectId}`;

        try {
            const response = await fetch(endpoint, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.status === 404) {
                alert("プロジェクトが見つかりません。");
                return null;
            }
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('プロジェクト詳細の取得に失敗:', error);
            alert("プロジェクト詳細の読み込みに失敗しました。");
            return null;
        }
    }


    /**
     * APIからプロジェクトを取得してレンダリングするメイン関数
     */
    const fetchAndRenderProjects = async (filters = {}) => {
        const { query, skill_id } = filters;
        const url = new URL('projects', API_BASE_URL + '/');

        if (query) { url.searchParams.append('query', query); }
        if (skill_id) { url.searchParams.append('skill_id', skill_id); }

        projectGrid.innerHTML = '<p>Loading projects...</p>';

        try {
            const token = localStorage.getItem('access_token');
            const headers = { 'Content-Type': 'application/json' };
            if (token) { headers['Authorization'] = `Bearer ${token}`; }

            const response = await fetch(url.toString(), {
                method: 'GET', headers: headers
            });

            if (!response.ok) { throw new Error(`Failed to fetch projects: ${response.statusText}`); }

            const data = await response.json();
            renderProjects(data.projects);
            resultCountSpan.textContent = `${data.total} projects found`;

        } catch (error) {
            console.error('Error fetching projects:', error);
            projectGrid.innerHTML = '<p class="error-message">Failed to load projects.</p>';
            resultCountSpan.textContent = '0 projects found';
        }
    };


    // --- UI レンダリング関数 ---

    /**
     * プロジェクト詳細モーダルを開く
     */
    async function openDetailModal(projectId) {
        // 詳細をロード
        const project = await fetchProjectDetails(projectId);
        if (!project) return;

        // --- モーダルに詳細情報をセット ---
        document.getElementById('detail-project-title').textContent = escapeHTML(project.title);
        document.getElementById('detail-description').innerHTML = `<strong>Description:</strong> ${escapeHTML(project.description)}`;

        // スキルリストを生成
        const skillsContainer = document.getElementById('detail-required-skills');
        skillsContainer.innerHTML = project.required_skills.map(skill =>
            `<span class="skill-badge">${escapeHTML(skill.skill_name)} (Lv.${skill.required_level})</span>`
        ).join('');

        // ステータスバッジ
        const statusBadge = document.getElementById('detail-status-badge');
        statusBadge.textContent = project.status.toUpperCase();
        statusBadge.className = `status-badge status-${project.status}`;

        // オーナー情報をセット (オーナーハンドル名は UserResponse から取得する必要があるため、一旦IDを表示)
        document.getElementById('detail-owner-handle').textContent = `Owner ID: ${project.owner_id}`;

        // 応募フォームにIDをセット
        applyProjectIdInput.value = projectId;
        applyFormError.style.display = 'none';

        detailModal.classList.add('visible');
    }

    /**
     * プロジェクト一覧を描画し、クリックイベントを設定
     */
    const renderProjects = (projects) => {
        projectGrid.innerHTML = '';
        if (projects.length === 0) {
            projectGrid.innerHTML = '<p>No projects found matching your criteria.</p>';
            return;
        }

        projects.forEach(project => {
            const card = document.createElement('div');
            card.className = 'project-card';
            card.setAttribute('data-project-id', project.id); // IDをデータ属性として保持

            const skillsHtml = project.required_skills.map(skill =>
                `<span class="skill-badge">${escapeHTML(skill.skill_name)}</span>`
            ).join('');

            // カードHTMLを生成
            card.innerHTML = `
                <div class="card-content">
                    <div class="card-meta">
                        <span class="card-status status-${project.status}">${project.status.toUpperCase()}</span>
                        <span class="card-date">${new Date(project.created_at).toLocaleDateString('ja-JP').replace(/\//g, '-')}</span>
                    </div>
                    <h4>${escapeHTML(project.title)}</h4>
                    <p>${escapeHTML(project.description)}</p>
                    <div class="card-skills">${skillsHtml}</div>
                </div>
            `;

            // ▼▼▼ クリックイベントを追加 ▼▼▼
            card.addEventListener('click', () => {
                openDetailModal(project.id);
            });

            projectGrid.appendChild(card);
        });
    };

    // --- 応募フォーム処理 ---

    async function handleApplicationSubmit(e) {
        e.preventDefault();

        const projectId = applyProjectIdInput.value;
        const message = document.getElementById('application-message').value;
        const token = localStorage.getItem('access_token');

        if (!token) {
            alert("ログインしてください。");
            window.location.href = '/public/login.html';
            return;
        }

        const endpoint = `${API_BASE_URL}/projects/${projectId}/applications`;
        const submitBtn = document.getElementById('submit-application-btn');
        applyFormError.style.display = 'none';

        submitBtn.disabled = true;
        submitBtn.textContent = '送信中...';

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message: message })
            });

            if (response.status === 201) {
                alert('応募が正常に送信されました！');
                detailModal.classList.remove('visible');
                applyForm.reset();
            } else {
                const errorData = await response.json();
                applyFormError.textContent = `エラー: ${errorData.detail || response.statusText}`;
                applyFormError.style.display = 'block';
            }
        } catch (error) {
            applyFormError.textContent = 'ネットワークエラーが発生しました。';
            applyFormError.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '応募を送信';
        }
    }


    // --- 初期化とイベントリスナー ---

    const getCurrentFilters = () => {
        const query = searchInput.value;
        let skill_id = null;
        if (skillFilterContainer) {
            const checkedBox = skillFilterContainer.querySelector('input[type="checkbox"]:checked');
            if (checkedBox) { skill_id = checkedBox.value; }
        }
        return { query, skill_id };
    }

    // ページ読み込み時にプロジェクトを取得
    fetchAndRenderProjects(getCurrentFilters());

    // イベントリスナー設定
    if (detailCloseBtn) detailCloseBtn.addEventListener('click', () => detailModal.classList.remove('visible'));
    if (detailModal) detailModal.addEventListener('click', (e) => {
        if (e.target === detailModal) detailModal.classList.remove('visible');
    });

    if (applyForm) applyForm.addEventListener('submit', handleApplicationSubmit);

    // 検索・フィルターイベント (変更なし)
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            fetchAndRenderProjects(getCurrentFilters());
        }
    });

    if (skillFilterContainer) {
        skillFilterContainer.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox') {
                const allCheckboxes = skillFilterContainer.querySelectorAll('input[type="checkbox"]');
                allCheckboxes.forEach(box => { if (box !== e.target) box.checked = false; });
                fetchAndRenderProjects(getCurrentFilters());
            }
        });
    }
});