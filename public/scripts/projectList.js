document.addEventListener('DOMContentLoaded', () => {

    // ▼▼▼ APIベースURLを関数の外に定義 ▼▼▼
    const API_BASE_URL = 'http://localhost:8080/api/v1';

    // --- 要素の取得 ---
    const projectGrid = document.getElementById('project-grid');
    const resultCountSpan = document.getElementById('result-count');
    const searchInput = document.getElementById('search-input');

    /**
     * APIからプロジェクトを取得してレンダリングするメイン関数
     */
    const fetchAndRenderProjects = async () => {
        // 検索クエリを取得
        const query = searchInput.value;

        // ▼▼▼ URLの構築方法を修正 ▼▼▼
        // 'http://localhost:8080/api/v1/' + 'projects' = 'http://localhost:8080/api/v1/projects' となるようにする
        const url = new URL('projects', API_BASE_URL + '/');
        // ▲▲▲ 修正ここまで ▲▲▲

        if (query) {
            url.searchParams.append('query', query);
        }
        // 他のフィルター（skill_id, statusなど）もここに追加可能
        // url.searchParams.append('skill_id', '123');

        // ローディング表示
        projectGrid.innerHTML = '<p>Loading projects...</p>';

        try {
            // (オプション) 認証トークンがあれば、「お気に入り」状態の取得に利用
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

            const data = await response.json(); // { projects: [], total: 0 }

            // プロジェクト一覧のレンダリング
            renderProjects(data.projects);

            // 件数の更新
            resultCountSpan.textContent = `${data.total} projects found`;

        } catch (error) {
            console.error('Error fetching projects:', error);
            projectGrid.innerHTML = '<p class="error-message">Failed to load projects. Please try again later.</p>';
            resultCountSpan.textContent = '0 projects found';
        }
    };

    /**
     * プロジェクトデータの配列を受け取り、HTMLを生成してグリッドに挿入する
     * @param {Array} projects - プロジェクトオブジェクトの配列
     */
    const renderProjects = (projects) => {
        // グリッドをクリア
        projectGrid.innerHTML = '';

        if (projects.length === 0) {
            projectGrid.innerHTML = '<p>No projects found matching your criteria.</p>';
            return;
        }

        projects.forEach(project => {
            // プロジェクトカードのHTMLを生成
            const card = document.createElement('div');
            card.className = 'project-card';

            // スキルバッジのHTMLを生成
            const skillsHtml = project.required_skills.map(skill =>
                `<span class="skill-badge">${skill.skill_name}</span>`
            ).join('');

            // 日付をフォーマット (例: 2024-01-15)
            const createdDate = new Date(project.created_at).toLocaleDateString('ja-JP', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            }).replace(/\//g, '-'); // ja-JPは yyyy/MM/dd を返すので '-' に置換

            card.innerHTML = `
                <img src="images/project_thumb_default.jpg" alt="${project.title}" class="card-image">
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

            // (オプション) お気に入り状態を反映
            if (project.is_favorited) {
                // 例: カードに 'favorited' クラスを追加
                // card.classList.add('favorited');
            }

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


    // --- イベントリスナー ---

    // 1. ページ読み込み時にプロジェクトを取得
    fetchAndRenderProjects();

    // 2. 検索ボックスでエンターキーが押されたら再検索
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // フォーム送信のキャンセル
            fetchAndRenderProjects();
        }
    });

    // 3. (将来的に) フィルタが変更されたら再検索
    // document.querySelector('.category-filter').addEventListener('change', fetchAndRenderProjects);
    // document.querySelector('.skill-filter').addEventListener('click', fetchAndRenderProjects);
});