// --- API呼び出しの設定 ---
// nginx経由でアクセスするため相対パスを使用
const API_BASE_URL = '/api/v1';

// --- グローバル変数 ---
let currentUserBio = "";
let currentUserSkills = [];
let modalSkills = [];
let searchTimer;

/**
 * XSS防止のための簡易HTMLエスケープ関数
 */
const escapeHTML = (str) => {
    if (!str) return '';
    return str.replace(/[&<>"']/g, (match) => {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
        return map[match];
    });
};

// --- 認証 & データ取得 ---
async function fetchMyInfo(tokenToUse) {
    const endpoint = `${API_BASE_URL}/auth/me`;
    console.log("リクエストを送信中...", endpoint);

    try {
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${tokenToUse}` }
        });

        if (response.ok) {
            const userData = await response.json();
            console.log("✅ 認証成功！ ユーザー情報:", userData);

            currentUserBio = userData.bio || "";
            updateProfileUI(userData);

            // [修正] handle ではなく id を渡す
            fetchMySkillsAndRepos(userData.id, tokenToUse);
            fetchMyProjects(userData.id, tokenToUse);

        } else {
            const errorData = await response.json();
            console.error(`❌ 認証失敗 (ステータス: ${response.status})`, errorData);
            localStorage.removeItem('access_token');
            window.location.href = '/login.html?error=invalid_token';
        }
    } catch (error) {
        console.error("ネットワークエラーが発生しました:", error);
    }
}

// --- スキルとリポジトリを取得 (UserDetailResponse) ---
async function fetchMySkillsAndRepos(userId, tokenToUse) {
    // [修正] /users/{id} (UUID) を呼び出す
    const endpoint = `${API_BASE_URL}/users/${userId}`;
    try {
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${tokenToUse}` }
        });
        if (!response.ok) throw new Error('Failed to fetch user details');

        const data = await response.json(); // UserDetailResponse
        console.log("✅ スキル・リポジトリ取得成功:", data);

        renderMySkills(data.skills);
        // renderMyRepos(data.repos);

    } catch (error) {
        console.error('Error fetching user details:', error);
        const listContainer = document.getElementById('profile-skills-list');
        if (listContainer) listContainer.innerHTML = '<p>スキルの読み込みに失敗しました。</p>';
    }
}

// --- プロフィールUI更新 (変更なし) ---
function updateProfileUI(userData) {
    const bioText = userData.bio || "自己紹介が設定されていません";
    if (document.getElementById('profile-name')) document.getElementById('profile-name').textContent = userData.handle;
    if (document.getElementById('profile-bio')) document.getElementById('profile-bio').textContent = bioText;
    if (document.getElementById('profile-about-text')) document.getElementById('profile-about-text').textContent = bioText;
    if (document.getElementById('contact-email')) document.getElementById('contact-email').innerHTML = `<i class="fa-solid fa-envelope"></i> ${userData.email || 'メール未設定'}`;
    if (document.getElementById('contact-github')) document.getElementById('contact-github').innerHTML = `<i class="fa-brands fa-github"></i> <a href="https://github.com/${userData.github_login}" target="_blank" rel="noopener noreferrer">/${userData.github_login}</a>`;
    if (document.getElementById('profile-avatar')) document.getElementById('profile-avatar').src = userData.avatar_url;
}

// --- プロジェクト取得・描画 (変更なし) ---
async function fetchMyProjects(ownerId, tokenToUse) {
    const listContainer = document.getElementById('profile-projects-list');
    if (!listContainer) return;
    listContainer.innerHTML = '<p>プロジェクトを読み込み中...</p>';
    const endpoint = `${API_BASE_URL}/projects?owner_id=${ownerId}`;
    try {
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${tokenToUse}` }
        });
        if (!response.ok) throw new Error('Failed to fetch projects');
        const data = await response.json();
        renderMyProjects(data.projects);
    } catch (error) {
        console.error('Error fetching projects:', error);
        listContainer.innerHTML = '<p>プロジェクトの読み込みに失敗しました。</p>';
    }
}
function renderMyProjects(projects) {
    const listContainer = document.getElementById('profile-projects-list');
    listContainer.innerHTML = '';
    if (projects.length === 0) {
        listContainer.innerHTML = '<p>あなたがオーナーのプロジェクトはまだありません。</p>';
        return;
    }
    projects.forEach(project => {
        const projectCard = document.createElement('div');
        projectCard.className = 'profile-project-card';
        const skillsHtml = project.required_skills.map(skill =>
            `<span class="skill-badge">${escapeHTML(skill.skill_name)}</span>`
        ).join('');
        projectCard.innerHTML = `
            <h4>${escapeHTML(project.title)}</h4>
            <p>${escapeHTML(project.description)}</p>
            <div class="card-skills">${skillsHtml}</div>
        `;
        listContainer.appendChild(projectCard);
    });
}

// --- スキルタブを描画する関数 (変更なし) ---
function renderMySkills(skills) {
    const listContainer = document.getElementById('profile-skills-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';

    currentUserSkills = skills.map(s => ({
        skill_id: s.skill_id,
        skill_name: s.skill_name,
        level: s.level
    }));

    if (currentUserSkills.length === 0) {
        listContainer.innerHTML = '<p>スキルが設定されていません。「Edit Skills」から追加できます。</p>';
        return;
    }

    currentUserSkills.forEach(skill => {
        const skillItem = document.createElement('div');
        skillItem.className = 'skill-item';
        skillItem.innerHTML = `
            <span class="skill-item-name">${escapeHTML(skill.skill_name)}</span>
            <span class="skill-item-level">Level: ${skill.level}</span>
        `;
        listContainer.appendChild(skillItem);
    });
}

// --- Bioプロフ編集モーダル ---
// [修正] 'const' 定義は DOMContentLoaded の中に移動

function openBioEditModal() {
    const bioTextarea = document.getElementById('bio-textarea');
    bioTextarea.value = currentUserBio;
    document.getElementById('edit-profile-modal').classList.add('visible');
}
function closeBioEditModal() {
    document.getElementById('edit-profile-modal').classList.remove('visible');
}

async function updateBio(tokenToUse, newBio) {
    const bioSaveBtn = document.getElementById('modal-save-btn');
    const endpoint = `${API_BASE_URL}/users/me`;
    bioSaveBtn.disabled = true;
    bioSaveBtn.textContent = "保存中...";
    document.getElementById('modal-error-message').style.display = 'none';
    try {
        const response = await fetch(endpoint, {
            method: 'PATCH',
            headers: { 'Authorization': `Bearer ${tokenToUse}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ "bio": newBio })
        });
        if (response.ok) {
            const updatedUserData = await response.json();
            currentUserBio = updatedUserData.bio;
            updateProfileUI(updatedUserData);
            closeBioEditModal();
        } else {
            const errorData = await response.json();
            document.getElementById('modal-error-message').textContent = `エラー: ${errorData.detail || '保存に失敗しました。'}`;
            document.getElementById('modal-error-message').style.display = 'block';
        }
    } catch (error) {
        document.getElementById('modal-error-message').textContent = "ネットワークエラーが発生しました。";
        document.getElementById('modal-error-message').style.display = 'block';
    } finally {
        bioSaveBtn.disabled = false;
        bioSaveBtn.textContent = "保存する";
    }
}

// --- スキル編集モーダルのロジック ---
// [修正] 'const' 定義は DOMContentLoaded の中に移動

function openSkillsModal() {
    modalSkills = [...currentUserSkills];
    renderSelectedSkillsList();
    document.getElementById('skill-modal-error').style.display = 'none';
    document.getElementById('skill-search-input').value = '';
    document.getElementById('skill-search-results').style.display = 'none';
    document.getElementById('edit-skills-modal').classList.add('visible');
}
function closeSkillsModal() {
    document.getElementById('edit-skills-modal').classList.remove('visible');
}

async function searchSkillsAPI(query) {
    const skillSearchResults = document.getElementById('skill-search-results');
    if (!query) {
        skillSearchResults.style.display = 'none';
        return;
    }
    try {
        const endpoint = `${API_BASE_URL}/skills?query=${encodeURIComponent(query)}`;
        const response = await fetch(endpoint, { method: 'GET' });
        if (!response.ok) throw new Error('Skill search failed');
        const data = await response.json();
        renderSkillSearchResults(data.skills);
    } catch (error) {
        console.error('Skill search error:', error);
    }
}

function renderSkillSearchResults(skills) {
    const skillSearchResults = document.getElementById('skill-search-results');
    const searchInput = document.getElementById('skill-search-input');
    const searchQuery = searchInput ? searchInput.value.trim() : '';
    
    skillSearchResults.innerHTML = '';
    
    if (skills.length === 0 && searchQuery) {
        // 検索結果がない場合、新規作成ボタンを表示
        skillSearchResults.innerHTML = `
            <div class="skill-search-item skill-search-no-result">検索結果がありません</div>
            <div class="skill-search-item skill-create-btn" data-skill-name="${escapeHTML(searchQuery)}">
                <i class="fa-solid fa-plus"></i> 「${escapeHTML(searchQuery)}」を新規作成
            </div>
        `;
        skillSearchResults.style.display = 'block';
        return;
    }
    
    // 検索結果を表示
    skills.forEach(skill => {
        const item = document.createElement('div');
        item.className = 'skill-search-item';
        item.textContent = escapeHTML(skill.name);
        item.dataset.skillId = skill.id;
        item.dataset.skillName = escapeHTML(skill.name);
        skillSearchResults.appendChild(item);
    });
    
    // 検索語句と完全一致するスキルがない場合、新規作成ボタンも追加
    if (searchQuery && !skills.some(s => s.name.toLowerCase() === searchQuery.toLowerCase())) {
        const createBtn = document.createElement('div');
        createBtn.className = 'skill-search-item skill-create-btn';
        createBtn.dataset.skillName = escapeHTML(searchQuery);
        createBtn.innerHTML = `<i class="fa-solid fa-plus"></i> 「${escapeHTML(searchQuery)}」を新規作成`;
        skillSearchResults.appendChild(createBtn);
    }
    
    skillSearchResults.style.display = 'block';
}

function renderSelectedSkillsList() {
    const selectedSkillsList = document.getElementById('selected-skills-list');
    if (!selectedSkillsList) {
        console.error('Element with ID "selected-skills-list" not found.');
        return;
    }
    selectedSkillsList.innerHTML = '';
    if (modalSkills.length === 0) {
        selectedSkillsList.innerHTML = '<p>スキルが選択されていません。</p>';
        return;
    }
    modalSkills.forEach(skill => {
        const item = document.createElement('div');
        item.className = 'selected-skill-item';
        item.dataset.skillId = skill.skill_id;
        let levelOptions = '';
        for (let i = 1; i <= 5; i++) {
            levelOptions += `<option value="${i}" ${skill.level == i ? 'selected' : ''}>Lv. ${i}</option>`;
        }
        item.innerHTML = `
            <span class="selected-skill-item-name">${escapeHTML(skill.skill_name)}</span>
            <select class="skill-level-select">${levelOptions}</select>
            <button class="skill-remove-btn">削除</button>
        `;
        selectedSkillsList.appendChild(item);
    });
}

function addSkillToModalList(skillId, skillName) {
    const exists = modalSkills.some(s => s.skill_id == skillId);
    if (!exists) {
        modalSkills.push({
            skill_id: parseInt(skillId),
            skill_name: skillName,
            level: 1
        });
        renderSelectedSkillsList();
    }
    document.getElementById('skill-search-input').value = '';
    document.getElementById('skill-search-results').style.display = 'none';
}

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

// --- スキル保存 (saveSkills) のロジック ---
async function saveSkills(token) {
    const skillsSaveBtn = document.getElementById('skills-modal-save-btn');
    const skillModalError = document.getElementById('skill-modal-error');
    const endpoint = `${API_BASE_URL}/users/me/skills`;
    skillModalError.style.display = 'none';
    skillsSaveBtn.disabled = true;
    skillsSaveBtn.textContent = '保存中...';

    const payload = modalSkills.map(s => ({
        skill_id: s.skill_id,
        level: s.level
    }));

    try {
        const response = await fetch(endpoint, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const data = await response.json();
            console.log('✅ スキル更新成功:', data.message);

            const currentToken = localStorage.getItem('access_token');
            const userData = await (await fetch(`${API_BASE_URL}/auth/me`, { headers: { 'Authorization': `Bearer ${currentToken}` } })).json();

            fetchMySkillsAndRepos(userData.id, currentToken);
            closeSkillsModal();

        } else {
            const errorData = await response.json();
            console.error('❌ スキル更新失敗:', errorData);
            skillModalError.textContent = `エラー: ${errorData.detail || '保存に失敗しました。'}`;
            skillModalError.style.display = 'block';
        }
    } catch (error) {
        console.error('Skill save error:', error);
        skillModalError.textContent = 'ネットワークエラーが発生しました。';
        skillModalError.style.display = 'block';
    } finally {
        skillsSaveBtn.disabled = false;
        skillsSaveBtn.textContent = '保存する';
    }
}


// --- ▼▼▼ [修正] 実行ロジックとイベントリスナーを DOMContentLoaded の中に移動 ▼▼▼ ---
document.addEventListener('DOMContentLoaded', () => {

    // --- Bioモーダルのイベントリスナー設定 ---
    const bioModal = document.getElementById('edit-profile-modal');
    const bioEditBtn = document.getElementById('edit-profile-btn');
    const bioCloseBtn = document.getElementById('modal-close-btn');
    const bioSaveBtn = document.getElementById('modal-save-btn');

    if (bioEditBtn) bioEditBtn.addEventListener('click', openBioEditModal);
    if (bioCloseBtn) bioCloseBtn.addEventListener('click', closeBioEditModal);
    if (bioModal) bioModal.addEventListener('click', (e) => { if (e.target === bioModal) closeBioEditModal(); });
    if (bioSaveBtn) {
        bioSaveBtn.addEventListener('click', () => {
            const bioTextarea = document.getElementById('bio-textarea');
            const newBio = bioTextarea.value;
            const currentToken = localStorage.getItem('access_token');
            if (currentToken) updateBio(currentToken, newBio);
            else window.location.href = '/public/login.html';
        });
    }

    // --- スキルモーダルのイベントリスナー設定 ---
    const skillsModal = document.getElementById('edit-skills-modal');
    const skillsEditBtn = document.getElementById('edit-skills-btn');
    const skillsCloseBtn = document.getElementById('skills-modal-close-btn');
    const skillsSaveBtn = document.getElementById('skills-modal-save-btn');
    const skillSearchInput = document.getElementById('skill-search-input');
    const skillSearchResults = document.getElementById('skill-search-results');
    const selectedSkillsList = document.getElementById('selected-skills-list');

    if (skillsEditBtn) skillsEditBtn.addEventListener('click', openSkillsModal);
    if (skillsCloseBtn) skillsCloseBtn.addEventListener('click', closeSkillsModal);
    if (skillsModal) skillsModal.addEventListener('click', (e) => { if (e.target === skillsModal) closeSkillsModal(); });

    if (skillSearchInput) {
        skillSearchInput.addEventListener('input', () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                searchSkillsAPI(skillSearchInput.value);
            }, 300);
        });
    }
    if (skillSearchResults) {
        skillSearchResults.addEventListener('click', async (e) => {
            const item = e.target.closest('.skill-search-item');
            if (!item) return;
            
            // 既存のスキルをクリックした場合
            if (item.dataset.skillId) {
                addSkillToModalList(item.dataset.skillId, item.dataset.skillName);
            }
            // 新規作成ボタンをクリックした場合
            else if (item.classList.contains('skill-create-btn')) {
                const skillName = item.dataset.skillName;
                if (!skillName) return;
                
                // ボタンを無効化して二重送信を防止
                item.style.pointerEvents = 'none';
                item.style.opacity = '0.6';
                const originalText = item.innerHTML;
                item.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 作成中...';
                
                const newSkill = await createNewSkill(skillName);
                
                if (newSkill) {
                    // 作成成功したらモーダルリストに追加
                    addSkillToModalList(newSkill.id, newSkill.name);
                } else {
                    // 失敗した場合はボタンを元に戻す
                    item.style.pointerEvents = '';
                    item.style.opacity = '';
                    item.innerHTML = originalText;
                }
            }
        });
    }
    if (selectedSkillsList) {
        selectedSkillsList.addEventListener('click', (e) => {
            const skillItem = e.target.closest('.selected-skill-item');
            if (!skillItem) return;
            const skillId = parseInt(skillItem.dataset.skillId);
            if (e.target.classList.contains('skill-remove-btn')) {
                modalSkills = modalSkills.filter(s => s.skill_id !== skillId);
                renderSelectedSkillsList();
            }
        });
        selectedSkillsList.addEventListener('change', (e) => {
            const skillItem = e.target.closest('.selected-skill-item');
            if (e.target.classList.contains('skill-level-select')) {
                const skillId = parseInt(skillItem.dataset.skillId);
                const newLevel = parseInt(e.target.value);
                const skillToUpdate = modalSkills.find(s => s.skill_id === skillId);
                if (skillToUpdate) skillToUpdate.level = newLevel;
            }
        });
    }
    if (skillsSaveBtn) {
        skillsSaveBtn.addEventListener('click', () => {
            const token = localStorage.getItem('access_token');
            if (token) saveSkills(token);
            else window.location.href = '/public/login.html';
        });
    }

    // --- メインの実行ロジック ---
    function getTokenFromHash() {
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        return params.get('access_token');
    }
    let token = getTokenFromHash();
    if (token) {
        console.log("URLハッシュからトークンを取得しました。");
        localStorage.setItem('access_token', token);
        // ヘッダーコンポーネントに認証状態の変更を通知
        window.dispatchEvent(new Event('auth-state-changed'));
        window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
        fetchMyInfo(token);

    } else {
        console.log("URLハッシュにトークンなし。localStorageを確認します。");
        token = localStorage.getItem('access_token');
        if (token) {
            fetchMyInfo(token);
        } else {
            console.log("トークンが見つかりません。ログインページにリダイレクトします。");
            window.location.href = '/login.html';
        }
    }
});
// ▲▲▲ [修正] DOMContentLoaded の閉じタグ ▲▲▲