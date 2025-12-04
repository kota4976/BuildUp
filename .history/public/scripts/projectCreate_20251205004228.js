document.addEventListener('DOMContentLoaded', () => {

    // --- APIベースURL ---
    const API_BASE_URL = '/api/v1';

    // --- 要素の取得 ---
    const createProjectBtn = document.querySelector('.create-project-btn');
    const modal = document.getElementById('create-project-modal');
    const closeBtn = modal.querySelector('.close-btn');
    const form = document.getElementById('create-project-form');
    const skillsContainer = document.getElementById('skills-container');
    const addSkillBtn = document.getElementById('add-skill-btn');
    const formError = document.getElementById('form-error');

    // --- スキル管理用の変数 ---
    let selectedSkills = [];
    let searchTimer;

    // --- モーダル表示 ---
    createProjectBtn.addEventListener('click', () => {
        modal.style.display = 'block';
        selectedSkills = [];
        renderSelectedSkills();
        formError.style.display = 'none';
    });

    // --- モーダル非表示 (3パターン) ---
    // 1. 閉じるボタン
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    // 2. モーダル外のクリック
    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = 'none';
        }
    });
    // 3. Escapeキー
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            modal.style.display = 'none';
        }
    });


    // --- ヘルパー関数: HTMLエスケープ ---
    const escapeHTML = (str) => {
        if (!str) return '';
        return str.replace(/[&<>"']/g, (match) => {
            const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
            return map[match];
        });
    };

    // --- スキル検索関数 ---
    async function searchSkills(query) {
        const skillSearchResults = document.getElementById('project-skill-search-results');
        if (!query) {
            skillSearchResults.style.display = 'none';
            return;
        }
        try {
            const endpoint = `${API_BASE_URL}/skills?query=${encodeURIComponent(query)}`;
            const response = await fetch(endpoint, { method: 'GET' });
            if (!response.ok) throw new Error('Skill search failed');
            const data = await response.json();
            renderSkillSearchResults(data.skills, query);
        } catch (error) {
            console.error('Skill search error:', error);
        }
    }

    // --- スキル検索結果の描画 ---
    function renderSkillSearchResults(skills, searchQuery) {
        const skillSearchResults = document.getElementById('project-skill-search-results');
        skillSearchResults.innerHTML = '';

        if (skills.length === 0 && searchQuery) {
            skillSearchResults.innerHTML = `
                <div class="skill-search-item skill-search-no-result">検索結果がありません</div>
                <div class="skill-search-item skill-create-btn" data-skill-name="${escapeHTML(searchQuery)}">
                    <i class="fa-solid fa-plus"></i> 「${escapeHTML(searchQuery)}」を新規作成
                </div>
            `;
            skillSearchResults.style.display = 'block';
            return;
        }

        skills.forEach(skill => {
            const item = document.createElement('div');
            item.className = 'skill-search-item';
            item.textContent = escapeHTML(skill.name);
            item.dataset.skillId = skill.id;
            item.dataset.skillName = escapeHTML(skill.name);
            skillSearchResults.appendChild(item);
        });

        if (searchQuery && !skills.some(s => s.name.toLowerCase() === searchQuery.toLowerCase())) {
            const createBtn = document.createElement('div');
            createBtn.className = 'skill-search-item skill-create-btn';
            createBtn.dataset.skillName = escapeHTML(searchQuery);
            createBtn.innerHTML = `<i class="fa-solid fa-plus"></i> 「${escapeHTML(searchQuery)}」を新規作成`;
            skillSearchResults.appendChild(createBtn);
        }

        skillSearchResults.style.display = 'block';
    }

    // --- スキル作成関数 ---
    async function createNewSkill(skillName) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login.html';
            return null;
        }

        try {
            const endpoint = `${API_BASE_URL}/skills`;
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: skillName })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'スキルの作成に失敗しました');
            }

            const newSkill = await response.json();
            console.log('✅ スキル作成成功:', newSkill);
            return newSkill;

        } catch (error) {
            console.error('スキル作成エラー:', error);
            alert(`エラー: ${error.message}`);
            return null;
        }
    }

    // --- 選択されたスキルを表示 ---
    function renderSelectedSkills() {
        skillsContainer.innerHTML = '';
        if (selectedSkills.length === 0) {
            skillsContainer.innerHTML = '<p style="color: #999; font-size: 0.9rem;">スキルを検索して追加してください</p>';
            return;
        }
        selectedSkills.forEach(skill => {
            const skillRow = document.createElement('div');
            skillRow.className = 'skill-input-row';
            skillRow.dataset.skillId = skill.skill_id;

            let levelOptions = '';
            for (let i = 1; i <= 5; i++) {
                levelOptions += `<option value="${i}" ${skill.required_level == i ? 'selected' : ''}>Lv. ${i}</option>`;
            }

            skillRow.innerHTML = `
                <span class="skill-name-display">${escapeHTML(skill.skill_name)}</span>
                <select class="skill-level-select">${levelOptions}</select>
                <button type="button" class="remove-skill-btn">削除</button>
            `;
            skillsContainer.appendChild(skillRow);
        });
    }

    // --- スキルをリストに追加 ---
    function addSkillToList(skillId, skillName) {
        const exists = selectedSkills.some(s => s.skill_id == skillId);
        if (!exists) {
            selectedSkills.push({
                skill_id: parseInt(skillId),
                skill_name: skillName,
                required_level: 1
            });
            renderSelectedSkills();
        }
        document.getElementById('project-skill-search-input').value = '';
        document.getElementById('project-skill-search-results').style.display = 'none';
    }

    // --- スキル検索入力イベント ---
    const skillSearchInput = document.getElementById('project-skill-search-input');
    if (skillSearchInput) {
        skillSearchInput.addEventListener('input', () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                searchSkills(skillSearchInput.value);
            }, 300);
        });
    }

    // --- スキル検索結果クリックイベント ---
    const skillSearchResults = document.getElementById('project-skill-search-results');
    if (skillSearchResults) {
        skillSearchResults.addEventListener('click', async (e) => {
            const item = e.target.closest('.skill-search-item');
            if (!item) return;

            if (item.dataset.skillId) {
                addSkillToList(item.dataset.skillId, item.dataset.skillName);
            } else if (item.classList.contains('skill-create-btn')) {
                const skillName = item.dataset.skillName;
                if (!skillName) return;

                item.style.pointerEvents = 'none';
                item.style.opacity = '0.6';
                const originalText = item.innerHTML;
                item.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 作成中...';

                const newSkill = await createNewSkill(skillName);

                if (newSkill) {
                    addSkillToList(newSkill.id, newSkill.name);
                } else {
                    item.style.pointerEvents = '';
                    item.style.opacity = '';
                    item.innerHTML = originalText;
                }
            }
        });
    }

    // --- スキル削除とレベル変更 ---
    skillsContainer.addEventListener('click', (e) => {
        const skillRow = e.target.closest('.skill-input-row');
        if (!skillRow) return;

        if (e.target.classList.contains('remove-skill-btn')) {
            const skillId = parseInt(skillRow.dataset.skillId);
            selectedSkills = selectedSkills.filter(s => s.skill_id !== skillId);
            renderSelectedSkills();
        }
    });

    skillsContainer.addEventListener('change', (e) => {
        const skillRow = e.target.closest('.skill-input-row');
        if (e.target.classList.contains('skill-level-select')) {
            const skillId = parseInt(skillRow.dataset.skillId);
            const newLevel = parseInt(e.target.value);
            const skill = selectedSkills.find(s => s.skill_id === skillId);
            if (skill) skill.required_level = newLevel;
        }
    });


    // --- マークダウンプレビュー機能 ---
    const descriptionInput = document.getElementById('project-description');
    const descriptionPreview = document.getElementById('description-preview');

    if (descriptionInput && descriptionPreview) {
        descriptionInput.addEventListener('input', () => {
            const markdownText = descriptionInput.value;
            if (markdownText.trim()) {
                const htmlContent = DOMPurify.sanitize(marked.parse(markdownText));
                descriptionPreview.innerHTML = htmlContent;
                descriptionPreview.style.display = 'block';
            } else {
                descriptionPreview.style.display = 'none';
            }
        });
    }

    // --- フォーム送信処理 ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        formError.style.display = 'none';

        // 1. フォームからデータを取得
        const title = document.getElementById('project-title').value;
        const description = document.getElementById('project-description').value;

        // 2. スキルデータを取得
        if (selectedSkills.length === 0) {
            formError.textContent = '少なくとも1つのスキルを追加してください';
            formError.style.display = 'block';
            return;
        }

        const required_skills = selectedSkills.map(s => ({
            skill_id: s.skill_id,
            required_level: s.required_level
        }));

        // 3. APIリクエストのペイロードを作成
        const payload = {
            title,
            description,
            required_skills
        };

        // 4. 認証トークンを取得
        const token = localStorage.getItem('access_token');
        if (!token) {
            formError.textContent = 'ログインが必要です';
            formError.style.display = 'block';
            return;
        }

        // 5. APIにPOSTリクエストを送信
        try {
            const response = await fetch(`${API_BASE_URL}/projects`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (response.status === 201) {
                alert('プロジェクトが作成されました！');
                modal.style.display = 'none';
                form.reset();
                selectedSkills = [];
                renderSelectedSkills();
                // プロジェクト一覧を再読み込み
                location.reload();
            } else {
                const errorData = await response.json();
                formError.textContent = `エラー: ${errorData.detail || response.statusText}`;
                formError.style.display = 'block';
            }
        } catch (error) {
            console.error('Error creating project:', error);
            formError.textContent = '予期しないエラーが発生しました';
            formError.style.display = 'block';
        }
    });
});