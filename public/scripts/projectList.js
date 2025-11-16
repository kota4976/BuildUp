document.addEventListener('DOMContentLoaded', () => {

    // APIベースURLを関数の外に定義
    const API_BASE_URL = 'http://localhost:8080/api/v1';

    // --- 要素の取得 ---
    const projectGrid = document.getElementById('project-grid');
    const resultCountSpan = document.getElementById('result-count');
    const searchInput = document.getElementById('search-input');
    const skillFilterContainer = document.querySelector('.skill-filter');

    /**
     * APIからプロジェクトを取得してレンダリングするメイン関数
     * @param {Object} filters - 検索フィルター
     * @param {string | null} filters.query - 検索クエリ
     * @param {number | null} filters.skill_id - スキルID
     */
    const fetchAndRenderProjects = async (filters = {}) => {
        const { query, skill_id } = filters;
        const url = new URL('projects', API_BASE_URL + '/');

        if (query) {
            url.searchParams.append('query', query);
        }
        if (skill_id) {
            url.searchParams.append('skill_id', skill_id);
        }

        projectGrid.innerHTML = '<p>Loading projects...</p>';

        try {
            const token = localStorage.getItem('access_token');
            const headers = {
                'Content-Type': 'application/json',
            };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: headers
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch projects: ${response.statusText}`);
            }

            const data = await response.json();
            renderProjects(data.projects);
            resultCountSpan.textContent = `${data.total} projects found`;

        } catch (error) {
            console.error('Error fetching projects:', error);
            projectGrid.innerHTML = '<p class="error-message">Failed to load projects. Please try again later.</p>';
            resultCountSpan.textContent = '0 projects found';
        }
    };

    /**
     * プロジェクトデータの配列を受け取り、HTMLを生成してグリッドに挿入する
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

            const skillsHtml = project.required_skills.map(skill =>
                `<span class="skill-badge">${skill.skill_name}</span>`
            ).join('');

            const createdDate = new Date(project.created_at).toLocaleDateString('ja-JP', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            }).replace(/\//g, '-');

            // ▼▼▼ 修正点: <img> タグを削除しました ▼▼▼
            card.innerHTML = `
                <div class="card-content">
                    <div class="card-meta">
                        <span class="card-status ${project.status}">${project.status}</span>
                        <span class="card-date">${createdDate}</span>
                    </div>
                    <h4>${escapeHTML(project.title)}</h4>
                    <p>${escapeHTML(project.description)}</p>
                    <div class="card-skills">
                        ${skillsHtml}
                    </div>
                </div>
            `;
            // ▲▲▲ 修正ここまで ▲▲▲

            projectGrid.appendChild(card);
        });
    };

    /**
     * XSS防止のための簡易HTMLエスケープ関数
     */
    const escapeHTML = (str) => {
        return str.replace(/[&<>"']/g, (match) => {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return map[match];
        });
    };


    /**
     * 現在のフィルター状態をすべて読み取る関数
     */
    const getCurrentFilters = () => {
        const query = searchInput.value;

        let skill_id = null;
        if (skillFilterContainer) {
            const checkedBox = skillFilterContainer.querySelector('input[type="checkbox"]:checked');
            if (checkedBox) {
                skill_id = checkedBox.value;
            }
        }
        return { query, skill_id };
    }


    // --- イベントリスナー ---

    // 1. ページ読み込み時にプロジェクトを取得
    fetchAndRenderProjects(getCurrentFilters());

    // 2. 検索ボックスでエンターキーが押されたら再検索
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            fetchAndRenderProjects(getCurrentFilters());
        }
    });

    // 3. スキルフィルターの変更を監視
    if (skillFilterContainer) {
        skillFilterContainer.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox') {

                // (簡易版: 1つだけ選択可能にする)
                const allCheckboxes = skillFilterContainer.querySelectorAll('input[type="checkbox"]');
                allCheckboxes.forEach(box => {
                    if (box !== e.target) box.checked = false;
                });

                fetchAndRenderProjects(getCurrentFilters());
            }
        });
    }
});