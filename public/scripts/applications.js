// scripts/applications.js

// API設定
// nginx経由でアクセスするため相対パスを使用
const API_BASE_URL = '/api/v1';

// グローバル変数
let currentUser = null;
let currentTab = 'received';

/**
 * JWTトークンを取得
 */
function getAuthToken() {
    return localStorage.getItem('access_token');
}

/**
 * HTMLエスケープ (XSS防止)
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 現在のユーザー情報を取得
 */
async function getCurrentUser() {
    const token = getAuthToken();
    if (!token) {
        window.location.href = '/login.html';
        return null;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('認証チェックに失敗しました:', error);
        return null;
    }
}

/**
 * 応募一覧を取得する
 * @param {'received' | 'submitted'} type - 応募された(received)か、応募した(submitted)か
 */
async function fetchApplications(type) {
    const token = getAuthToken();
    if (!token) return { applications: [] };

    const endpoint = `${API_BASE_URL}/applications/me?type=${type}`;
    const loadingIndicator = document.getElementById('loading-indicator');
    const generalErrorDiv = document.getElementById('general-error-message');

    loadingIndicator.classList.remove('hidden');
    generalErrorDiv.classList.add('hidden');

    try {
        const response = await fetch(endpoint, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.status === 404) {
            return { applications: [] };
        }
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json(); // { applications: [...] }
    } catch (error) {
        console.error(`応募一覧の取得に失敗しました (${type}):`, error);
        generalErrorDiv.classList.remove('hidden');
        return { applications: [] };
    } finally {
        loadingIndicator.classList.add('hidden');
    }
}

/**
 * 応募の状態を変更する (承認/拒否)
 */
async function updateApplicationStatus(applicationId, action) {
    const token = getAuthToken();
    if (!token) return;

    const endpoint = `${API_BASE_URL}/applications/${applicationId}/${action}`;

    const card = document.querySelector(`[data-application-id="${applicationId}"]`);
    const actionBtns = card.querySelectorAll('.action-btn');
    actionBtns.forEach(btn => btn.disabled = true);


    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `処理中にエラーが発生しました。`);
        }

        // 成功した場合、リストをリロード
        await switchTab(currentTab);

    } catch (error) {
        alert(`処理に失敗しました: ${error.message}`);
    } finally {
        actionBtns.forEach(btn => btn.disabled = false);
    }
}


/**
 * 応募カードをレンダリング
 */
function renderApplications(applications, type) {
    const listContainer = document.getElementById(`${type}-list`);
    const noAppsDiv = document.getElementById(`no-${type}-apps`);

    if (!listContainer) return;

    listContainer.innerHTML = '';

    if (applications.length === 0) {
        noAppsDiv.classList.remove('hidden');
        return;
    }

    noAppsDiv.classList.add('hidden');

    applications.forEach(app => {
        const isReceived = type === 'received';

        const otherUser = isReceived ? app.applicant : app.project?.owner;
        const projectTitle = app.project?.title || 'プロジェクト情報が取得できません';

        const statusClass = `status-${app.status}`;
        const statusText = app.status === 'pending' ? '審査中' : (app.status === 'accepted' ? '承認済' : '却下済');

        const createdDate = new Date(app.created_at).toLocaleDateString('ja-JP');

        // アクションボタン
        let footerHtml = '';
        if (isReceived) {
            // 応募された場合 (オーナー)
            if (app.status === 'pending') {
                footerHtml = `
                    <button class="action-btn btn-primary" data-action="accept" data-id="${app.id}">
                        <i data-lucide="check" class="w-5 h-5"></i> 承認
                    </button>
                    <button class="action-btn btn-secondary text-red-600" data-action="reject" data-id="${app.id}">
                        <i data-lucide="x" class="w-5 h-5"></i> 却下
                    </button>
                `;
            } else if (app.status === 'accepted') { // ★★★ 修正: 承認済みの場合はチャットボタンを表示 ★★★
                footerHtml = `
                    <a href="/chat.html" class="action-btn btn-primary">
                        <i data-lucide="message-square" class="w-5 h-5"></i> チャットを開始
                    </a>
                `;
            } else {
                footerHtml = `<span class="text-sm text-gray-500">応募は既に${statusText}です。</span>`;
            }
        } else {
            // 応募した場合 (応募者)
            if (app.status === 'pending') {
                footerHtml = `<span class="text-sm text-gray-500">現在審査中です。</span>`;
            } else if (app.status === 'accepted') {
                footerHtml = `
                    <a href="/chat.html" class="action-btn btn-primary">
                        <i data-lucide="message-square" class="w-5 h-5"></i> チャットを開始
                    </a>
                 `;
            }
        }

        const cardHtml = `
            <div class="application-card" data-application-id="${app.id}">
                
                <div class="card-header">
                    <div class="project-info">
                        <h3>${escapeHtml(projectTitle)}</h3>
                        <p>${isReceived ? 'プロジェクトへ応募されました' : 'プロジェクトに応募しました'}</p>
                    </div>
                    <div class="status-badge ${statusClass}">${statusText}</div>
                </div>

                <div class="applicant-info">
                    <img src="${otherUser?.avatar_url || 'https://placehold.co/40x40/f0f0f0/666?text=U'}" alt="${otherUser?.handle || 'Unknown'}">
                    <div class="applicant-details">
                        <h4>${otherUser?.handle || 'Unknown User'}</h4>
                        <p>${isReceived ? '応募者' : 'プロジェクトオーナー'}</p>
                    </div>
                    <span class="text-sm text-gray-500 ml-auto">応募日: ${createdDate}</span>
                </div>
                
                <div class="application-message">
                    <p>「${escapeHtml(app.message)}」</p>
                </div>
                
                <div class="card-footer">
                    ${footerHtml}
                </div>
            </div>
        `;
        listContainer.insertAdjacentHTML('beforeend', cardHtml);
    });

    // イベントリスナーの再登録 (承認/拒否ボタン)
    if (type === 'received') {
        document.querySelectorAll(`#received-list button.action-btn[data-action]`).forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                const appId = e.currentTarget.dataset.id;

                if (confirm(`本当にこの応募を「${action === 'accept' ? '承認' : '拒否'}」しますか？`)) {
                    updateApplicationStatus(appId, action);
                }
            });
        });
    }

    lucide.createIcons();
}


/**
 * タブ切り替えとAPI呼び出しのメインロジック
 */
async function switchTab(targetType) {
    currentTab = targetType;

    // タブのアクティブクラス切り替え
    document.querySelectorAll('.tabs button').forEach(btn => {
        if (btn.dataset.type === targetType) {
            btn.classList.add('active-tab');
        } else {
            btn.classList.remove('active-tab');
        }
    });

    // コンテンツの表示/非表示を切り替える
    document.getElementById('received-content').classList.toggle('hidden', targetType !== 'received');
    document.getElementById('submitted-content').classList.toggle('hidden', targetType !== 'submitted');

    // データのフェッチとレンダリング
    const data = await fetchApplications(targetType);
    renderApplications(data.applications, targetType);
}


/**
 * 初期化
 */
document.addEventListener('DOMContentLoaded', async () => {
    // 認証チェック
    currentUser = await getCurrentUser();
    if (!currentUser) return; // 認証失敗時はリダイレクト済み

    // タブイベントリスナーの設定
    document.getElementById('tab-received').addEventListener('click', () => switchTab('received'));
    document.getElementById('tab-submitted').addEventListener('click', () => switchTab('submitted'));

    // 初回ロード ('received'タブ)
    await switchTab('received');
});

// Lucide IconsをDOM操作後に初期化
if (typeof lucide !== 'undefined') { lucide.createIcons(); }