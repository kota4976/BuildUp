/**
 * chatCreate.js
 * チャット作成モーダル、ユーザー検索、およびチャット作成API呼び出しを処理
 */

// 外部依存 (chat.js から引き継ぎ - モジュール外のAPI_BASE_URLに依存)
const API_HOST_PORT = 'localhost:8080';
const API_BASE_URL = `http://${API_HOST_PORT}/api/v1`;

// グローバル変数 (外部から参照/更新される可能性のある状態変数)
// ※ selectedMembers のみ、このモジュール内で完結するため export しません。
let selectedMembers = new Set(); // グループチャット用の選択メンバー


// 外部関数 (chat.js からインポートされることを想定)
// NOTE: getAuthToken, showError は外部ファイルで export されていることを前提とします。
//       getUserInfo は、依存オブジェクト経由で渡されることを前提とします。
function getAuthToken() {
    // 外部ファイルからインポートされていることを想定
    return window.getAuthToken();
}
function showError(message) {
    // 外部ファイルからインポートされていることを想定
    window.showError(message);
}


// --- API関数 (exportを追加) ---

/**
 * ユーザーを検索
 * @returns {Array<object>} ユーザーリスト
 */
export async function searchUsers(query) {
    try {
        // グローバルスコープの getAuthToken を呼び出す
        const token = getAuthToken();
        if (!token) {
            showError('ユーザー検索には認証が必要です。');
            throw new Error('認証トークンがありません');
        }

        const response = await fetch(`${API_BASE_URL}/users/search?q=${encodeURIComponent(query)}&limit=10`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            // エラーハンドリング強化: サーバーが返すエラーメッセージを取得
            let errorDetail = `HTTPエラー: ${response.status}`;
            try {
                const errorData = await response.json();
                errorDetail = errorData.message || errorDetail;

                // "Not authenticated" エラーの場合、認証失敗として特別扱い
                if (errorDetail === "Not authenticated") {
                    errorDetail = "認証トークンが無効または期限切れです。ログインし直してください。";
                }
            } catch (e) { /* JSON解析エラーは無視 */ }

            showError(`ユーザー検索に失敗しました: ${errorDetail}`);
            throw new Error(`HTTP error! status: ${response.status}. Detail: ${errorDetail}`);
        }

        const data = await response.json();
        // 以前表示されたかもしれないエラーメッセージをクリア
        document.getElementById('chat-list-error')?.classList.add('hidden');
        return data.users || [];
    } catch (error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('ERR_BLOCKED_BY_CLIENT')) {
            showError('ネットワーク接続エラー、またはAPIサーバーが停止/CORSブロックされています。');
        } else if (!error.message.startsWith('HTTP error')) {
            showError(`予期せぬエラー: ${error.message}`);
        }
        console.error('ユーザー検索に失敗しました:', error);
        return [];
    }
}

/**
 * ダイレクトチャットを作成
 */
export async function createDirectChat(targetUserId) {
    try {
        const token = getAuthToken();
        if (!token) {
            throw new Error('認証トークンがありません');
        }

        const response = await fetch(`${API_BASE_URL}/matches/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_user_id: targetUserId
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.match;
    } catch (error) {
        console.error('ダイレクトチャットの作成に失敗しました:', error);
        throw error;
    }
}

/**
 * グループチャットを作成
 */
export async function createGroupChat(groupName, memberIds) {
    try {
        const token = getAuthToken();
        if (!token) {
            throw new Error('認証トークンがありません');
        }

        const response = await fetch(`${API_BASE_URL}/groups`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: groupName,
                member_ids: Array.from(memberIds)
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.group;
    } catch (error) {
        console.error('グループチャットの作成に失敗しました:', error);
        throw error;
    }
}


// --- DOM操作・ロジック関数 ---

/**
 * ユーザー検索結果を表示
 */
function displayUserSearchResults(users, containerId, isGroup = false) {
    const container = document.getElementById(containerId);

    if (users.length === 0) {
        container.innerHTML = '<div class="p-3 text-gray-500 text-sm">該当するユーザーが見つかりません</div>';
        container.classList.remove('hidden');
        return;
    }

    container.innerHTML = users.map(user => `
        <div class="p-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 cursor-pointer transition-colors user-search-result" 
             data-user-id="${user.id}" 
             data-user-name="${user.handle}" 
             data-user-avatar="${user.avatar_url || 'https://placehold.co/32x32/f0f0f0/666?text=U'}">
            <div class="flex items-center">
                <img src="${user.avatar_url || 'https://placehold.co/32x32/f0f0f0/666?text=U'}" 
                     alt="${user.handle}" 
                     class="w-8 h-8 rounded-full mr-3 border border-gray-200"
                     onerror="this.onerror=null; this.src='https://placehold.co/32x32/f0f0f0/666?text=U'">
                <div class="flex-1 min-w-0">
                    <div class="font-medium text-gray-900 truncate">${user.handle}</div>
                    <div class="text-xs text-gray-500 truncate">${user.name || ''}</div>
                </div>
                ${isGroup ? '<button type="button" class="ml-2 px-3 py-1 bg-blue-600 text-white text-xs rounded-full hover:bg-blue-700 transition-colors add-member-btn">追加</button>' : ''}
            </div>
        </div>
    `).join('');

    container.classList.remove('hidden');
}

/**
 * 選択されたメンバーを表示
 */
function renderSelectedMembers() {
    const container = document.getElementById('selected-members-list');

    if (selectedMembers.size === 0) {
        container.innerHTML = '<p class="text-gray-500 text-sm text-center">メンバーが選択されていません</p>';
        return;
    }

    // 選択されたメンバーの情報を取得して表示
    const memberPromises = Array.from(selectedMembers).map(userId =>
        window.getUserInfo(userId).then(user => ({ id: userId, user })) // 依存性注入された getUserInfo を利用
    );

    Promise.all(memberPromises).then(members => {
        container.innerHTML = members.map(({ id, user }) => `
            <div class="flex items-center justify-between p-2 bg-white rounded-lg border border-gray-200 mb-2 last:mb-0">
                <div class="flex items-center">
                    <img src="${user.avatar_url || 'https://placehold.co/32x32/f0f0f0/666?text=U'}" 
                         alt="${user.handle}" 
                         class="w-8 h-8 rounded-full mr-3 border border-gray-200"
                         onerror="this.onerror=null; this.src='https://placehold.co/32x32/f0f0f0/666?text=U'">
                    <div class="flex-1 min-w-0">
                        <div class="font-medium text-gray-900 text-sm truncate">${user.handle}</div>
                    </div>
                </div>
                <button type="button" class="text-red-500 hover:text-red-700 remove-member-btn" data-user-id="${id}">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
        `).join('');

        // アイコンを初期化
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    });
}

/**
 * チャット作成モーダルを初期化 (外部公開用)
 * @param {object} dependencies 外部依存関数と変数を含むオブジェクト
 */
export function initChatCreationModal(dependencies) {
    const {
        currentUser,
        renderMatchList,
        selectMatch,
        selectGroupChat,
        matches,
        getAuthToken: importedGetAuthToken, // getAuthToken をインポート
        showError: importedShowError,       // showError をインポート
        getUserInfo: importedGetUserInfo     // getUserInfo をインポート
    } = dependencies;

    // 外部依存関数をウィンドウオブジェクトに一時的に設定
    // ※ clean up が難しいため推奨されない方法ですが、依存関係を解決するため使用
    window.currentUser = currentUser;
    window.getAuthToken = importedGetAuthToken;
    window.showError = importedShowError;
    window.getUserInfo = importedGetUserInfo;

    // NOTE: userCache は chat.js からインポート/エクスポートして利用してください。

    const modal = document.getElementById('create-chat-modal');
    const createChatBtn = document.getElementById('create-chat-btn');
    const closeModalBtn = document.getElementById('close-chat-modal');
    const directTab = document.getElementById('tab-direct');
    const groupTab = document.getElementById('tab-group');
    const directForm = document.getElementById('direct-chat-form');
    const groupForm = document.getElementById('group-chat-form');
    const userSearch = document.getElementById('user-search');
    const groupUserSearch = document.getElementById('group-user-search');
    const cancelDirectBtn = document.getElementById('cancel-direct-chat');
    const cancelGroupBtn = document.getElementById('cancel-group-chat');

    // モーダルを開く
    createChatBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
        switchToDirectChat();
    });

    // モーダルを閉じる
    function closeModal() {
        modal.classList.add('hidden');
        resetForms();
    }

    closeModalBtn.addEventListener('click', closeModal);
    cancelDirectBtn.addEventListener('click', closeModal);
    cancelGroupBtn.addEventListener('click', closeModal);

    // 背景クリックで閉じる
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // タブ切り替え
    directTab.addEventListener('click', switchToDirectChat);
    groupTab.addEventListener('click', switchToGroupChat);

    function switchToDirectChat() {
        directTab.classList.add('border-blue-600', 'text-blue-600');
        directTab.classList.remove('border-transparent', 'text-gray-500');
        groupTab.classList.add('border-transparent', 'text-gray-500');
        groupTab.classList.remove('border-blue-600', 'text-blue-600');
        directForm.classList.remove('hidden');
        groupForm.classList.add('hidden');
    }

    function switchToGroupChat() {
        groupTab.classList.add('border-blue-600', 'text-blue-600');
        groupTab.classList.remove('border-transparent', 'text-gray-500');
        directTab.classList.add('border-transparent', 'text-gray-500');
        directTab.classList.remove('border-blue-600', 'text-blue-600');
        groupForm.classList.remove('hidden');
        directForm.classList.add('hidden');
    }

    // ユーザー検索（ダイレクトチャット）
    let userSearchTimeout;
    userSearch.addEventListener('input', (e) => {
        clearTimeout(userSearchTimeout);
        const query = e.target.value.trim();

        if (query.length < 2) {
            document.getElementById('user-search-results').classList.add('hidden');
            return;
        }

        userSearchTimeout = setTimeout(async () => {
            const users = await searchUsers(query);
            displayUserSearchResults(users, 'user-search-results', false);
        }, 300);
    });

    // ユーザー検索（グループチャット）
    let groupUserSearchTimeout;
    groupUserSearch.addEventListener('input', (e) => {
        clearTimeout(groupUserSearchTimeout);
        const query = e.target.value.trim();

        if (query.length < 2) {
            document.getElementById('group-user-search-results').classList.add('hidden');
            return;
        }

        groupUserSearchTimeout = setTimeout(async () => {
            const users = await searchUsers(query);
            displayUserSearchResults(users, 'group-user-search-results', true);
        }, 300);
    });

    // ユーザー選択（ダイレクトチャット）
    document.addEventListener('click', (e) => {
        if (e.target.closest('.user-search-result') && !e.target.classList.contains('add-member-btn')) {
            const userItem = e.target.closest('.user-search-result');
            const userId = userItem.getAttribute('data-user-id');
            const userName = userItem.getAttribute('data-user-name');
            const userAvatar = userItem.getAttribute('data-user-avatar');

            document.getElementById('selected-user-id').value = userId;
            document.getElementById('selected-user-name').textContent = userName;
            document.getElementById('selected-user-handle').textContent = userName;
            document.getElementById('selected-user-avatar').src = userAvatar;
            document.getElementById('selected-user').classList.remove('hidden');
            document.getElementById('user-search-results').classList.add('hidden');
            userSearch.value = '';
        }
    });

    // ユーザー選択解除（ダイレクトチャット）
    document.getElementById('remove-selected-user').addEventListener('click', () => {
        document.getElementById('selected-user').classList.add('hidden');
        document.getElementById('selected-user-id').value = '';
    });

    // メンバー追加（グループチャット）
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('add-member-btn')) {
            const userItem = e.target.closest('.user-search-result');
            const userId = userItem.getAttribute('data-user-id');

            // 自分自身は追加しない
            if (userId === currentUser.id) {
                return;
            }

            selectedMembers.add(userId);
            renderSelectedMembers();
            document.getElementById('group-user-search-results').classList.add('hidden');
            groupUserSearch.value = '';
        }
    });

    // メンバー削除（グループチャット）
    document.addEventListener('click', (e) => {
        if (e.target.closest('.remove-member-btn')) {
            const button = e.target.closest('.remove-member-btn');
            const userId = button.getAttribute('data-user-id');
            selectedMembers.delete(userId);
            renderSelectedMembers();
        }
    });

    // ダイレクトチャット作成
    directForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const targetUserId = document.getElementById('selected-user-id').value;
        if (!targetUserId) {
            showFormError('direct-chat-error', 'ユーザーを選択してください');
            return;
        }

        const submitBtn = directForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = '作成中...';

        try {
            const match = await createDirectChat(targetUserId);
            closeModal();

            // 新しいチャットをリストに追加
            matches.push(match);
            await renderMatchList(matches);

            // 作成したチャットを選択
            const otherUser = await window.getUserInfo(targetUserId); // 依存性注入された getUserInfo を利用
            selectMatch(match, otherUser);

        } catch (error) {
            showFormError('direct-chat-error', error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'チャットを開始';
        }
    });

    // グループチャット作成
    groupForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const groupName = document.getElementById('group-name').value.trim();
        if (!groupName) {
            showFormError('group-chat-error', 'グループ名を入力してください');
            return;
        }

        if (selectedMembers.size === 0) {
            showFormError('group-chat-error', '少なくとも1人のメンバーを追加してください');
            return;
        }

        const submitBtn = groupForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = '作成中...';

        try {
            const group = await createGroupChat(groupName, selectedMembers);
            closeModal();

            // 新しいグループチャットをリストに追加
            const groupMatch = {
                id: group.id,
                is_group_chat: true,
                group_info: {
                    name: group.name,
                    avatar_url: group.avatar_url,
                    member_count: group.member_count
                }
            };
            matches.push(groupMatch);
            await renderMatchList(matches);

            // 作成したグループチャットを選択
            selectGroupChat(groupMatch, groupMatch.group_info);

        } catch (error) {
            showFormError('group-chat-error', error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'グループを作成';
        }
    });

    function showFormError(formId, message) {
        const errorElement = document.getElementById(formId);
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }

    function resetForms() {
        // ダイレクトチャットフォームをリセット
        document.getElementById('user-search').value = '';
        document.getElementById('selected-user').classList.add('hidden');
        document.getElementById('selected-user-id').value = '';
        document.getElementById('user-search-results').classList.add('hidden');
        document.getElementById('direct-chat-error').classList.add('hidden');

        // グループチャットフォームをリセット
        document.getElementById('group-name').value = '';
        document.getElementById('group-user-search').value = '';
        document.getElementById('group-user-search-results').classList.add('hidden');
        selectedMembers.clear();
        renderSelectedMembers();
        document.getElementById('group-chat-error').classList.add('hidden');
    }
}