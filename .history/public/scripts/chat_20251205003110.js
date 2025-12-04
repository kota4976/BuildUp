/**
 * チャット機能のJavaScript
 * APIとWebSocketに接続してリアルタイムチャットを実現
 * (チャット作成ロジックは外部ファイルに分離されています)
 */

// WebRTCマネージャーをインポート
import { webrtcManager } from './webrtc.js';

// API設定
// nginx経由でアクセスするため相対パスを使用
const API_BASE_URL = '/api/v1';
// WebSocket URLも相対パスを使用
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_BASE_URL = `${WS_PROTOCOL}//${window.location.host}/ws`;

// グローバル変数 (exportを追加)
export let currentUser = null;
let currentMatchId = null;
let currentConversationId = null;
let currentIsGroupChat = false;  // 現在のチャットがグループチャットかどうか
let websocket = null;
export let matches = []; // 外部（chatCreate.js）で更新されるためexport
export let userCache = {}; // 外部（chatCreate.js）で利用されるためexport
let currentOtherUserId = null;  // 現在のチャット相手のユーザーID
let currentPartnerName = null;  // 現在のチャット相手の名前

/**
 * 現在のWebSocket接続を取得（WebRTC用）
 */
window.getCurrentWebSocket = function () {
    return websocket;
};

/**
 * JWTトークンを取得 (exportを追加)
 */
export function getAuthToken() {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
}

/**
 * 現在のユーザー情報を取得
 */
async function getCurrentUser() {
    try {
        const token = getAuthToken();
        if (!token) {
            throw new Error('認証トークンがありません');
        }

        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login.html';
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('現在のユーザー情報の取得に失敗しました:', error);
        // グローバルな showError を直接呼び出す
        showError('認証に失敗しました。 <a href="/login.html">ログイン</a> してください。');
        return null;
    }
}

/**
 * ユーザー情報を取得（キャッシュ付き） (exportを追加)
 */
export async function getUserInfo(userId) {
    if (userCache[userId]) {
        return userCache[userId];
    }

    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
            headers: { 'Authorization': `Bearer ${getAuthToken()}` }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const user = await response.json();
        userCache[userId] = user;
        return user;
    } catch (error) {
        console.error('ユーザー情報の取得に失敗しました:', error);
        // グローバルな showError を直接呼び出す
        showError('ユーザー情報の取得に失敗しました。');
        return {
            id: userId,
            handle: 'Unknown User',
            avatar_url: 'https://placehold.co/48x48/f0f0f0/666?text=U'
        };
    }
}

// ---------------------------------------------------------------------

/**
 * マッチ（1対1）とグループチャット一覧を取得
 */
async function fetchMatches() {
    try {
        const token = getAuthToken();
        if (!token) {
            throw new Error('認証トークンがありません');
        }

        const headers = { 'Authorization': `Bearer ${token}` };

        const [matchesResponse, groupsResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/matches/me/matches`, { headers }),
            fetch(`${API_BASE_URL}/group-chats`, { headers })
        ]);

        if (matchesResponse.status === 401 || groupsResponse.status === 401) {
            window.location.href = '/login.html';
            return [];
        }

        if (!matchesResponse.ok) {
            throw new Error(`マッチ一覧の取得に失敗しました (status: ${matchesResponse.status})`);
        }

        const matchesData = await matchesResponse.json();
        const directMatches = (matchesData.matches || []).map(match => ({
            ...match,
            is_group_chat: false
        }));

        if (!groupsResponse.ok) {
            const message = await extractErrorMessage(groupsResponse, 'グループチャット一覧の取得に失敗しました。');
            throw new Error(message);
        }

        const groupData = await groupsResponse.json();
        const groupMatches = Array.isArray(groupData)
            ? groupData.map(group => ({
                id: group.id,
                is_group_chat: true,
                group_info: {
                    name: group.name,
                    avatar_url: group.avatar_url || null,
                    member_count: group.members ? group.members.length : 0
                },
                members: group.members || [],
                created_at: group.created_at,
                updated_at: group.updated_at
            }))
            : [];

        return [...directMatches, ...groupMatches];
    } catch (error) {
        console.error('チャット一覧の取得に失敗しました:', error);
        showError(error.message || 'チャット一覧の取得に失敗しました。');
        return [];
    }
}

/**
 * Fetchレスポンスからエラーメッセージを抽出
 */
async function extractErrorMessage(response, fallbackMessage) {
    try {
        const data = await response.json();
        if (data?.detail) {
            return data.detail;
        }
        if (data?.message) {
            return data.message;
        }
    } catch (e) {
        // JSON以外のレスポンスの場合は無視
    }
    return fallbackMessage;
}

/**
 * 会話履歴を取得
 * @param {string} matchId - マッチIDまたはグループチャットID
 * @param {boolean} isGroupChat - グループチャットの場合true
 */
async function fetchConversation(matchId, isGroupChat = false) {
    try {
        const token = getAuthToken();
        if (!token) {
            throw new Error('認証トークンがありません');
        }

        // グループチャットとダイレクトチャットで異なるエンドポイントを使用
        const endpoint = isGroupChat
            ? `${API_BASE_URL}/group-chats/${matchId}?limit=50`
            : `${API_BASE_URL}/matches/${matchId}/conversation?limit=50`;

        const response = await fetch(endpoint, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login.html';
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('会話履歴の取得に失敗しました:', error);
        // グローバルな showError を直接呼び出す
        showError('会話履歴の取得に失敗しました。');
        return null;
    }
}

/**
 * マッチ一覧をレンダリング (exportを追加)
 */
export async function renderMatchList(matches) {
    const container = document.getElementById('message-container');
    const loading = document.getElementById('chat-list-loading');
    const error = document.getElementById('chat-list-error');

    if (matches.length === 0) {
        loading.innerHTML = '<div class="text-gray-500 text-center p-8">チャットがありません</div>';
        return;
    }

    loading.style.display = 'none';
    error.classList.add('hidden');
    container.innerHTML = '';

    // 各マッチに対して会話履歴を取得してプレビューを表示
    const matchPromises = matches.map(async (match) => {
        try {
            // グループチャットかどうかを判定
            if (match.is_group_chat) {
                // グループチャットの場合
                const groupInfo = match.group_info || {};
                let lastMessage = null;

                try {
                    const conversation = await fetchConversation(match.id, true);  // グループチャットフラグを渡す
                    if (conversation && conversation.messages && conversation.messages.length > 0) {
                        lastMessage = conversation.messages[conversation.messages.length - 1];
                    }
                } catch (error) {
                    console.warn(`会話履歴の取得に失敗しました (match_id: ${match.id}):`, error);
                }

                return {
                    match,
                    isGroup: true,
                    groupInfo,
                    lastMessage
                };
            } else {
                // ダイレクトチャットの場合
                const otherUserId = match.user_a === currentUser.id ? match.user_b : match.user_a;
                const otherUser = await getUserInfo(otherUserId);
                let lastMessage = null;

                try {
                    const conversation = await fetchConversation(match.id, false);  // ダイレクトチャットフラグを渡す
                    if (conversation && conversation.messages && conversation.messages.length > 0) {
                        lastMessage = conversation.messages[conversation.messages.length - 1];
                    }
                } catch (error) {
                    console.warn(`会話履歴の取得に失敗しました (match_id: ${match.id}):`, error);
                }

                return {
                    match,
                    isGroup: false,
                    otherUser,
                    lastMessage
                };
            }
        } catch (error) {
            console.error(`マッチ情報の取得に失敗しました (match_id: ${match.id}):`, error);
            return {
                match,
                isGroup: false,
                otherUser: {
                    id: 'unknown',
                    handle: 'Unknown User',
                    avatar_url: 'https://placehold.co/48x48/f0f0f0/666?text=U'
                },
                lastMessage: null
            };
        }
    });

    const matchDataList = await Promise.all(matchPromises);

    // 最新メッセージの時刻でソート（降順）
    matchDataList.sort((a, b) => {
        if (!a.lastMessage && !b.lastMessage) return 0;
        if (!a.lastMessage) return 1;
        if (!b.lastMessage) return -1;
        return new Date(b.lastMessage.created_at) - new Date(a.lastMessage.created_at);
    });

    // マッチアイテムを作成
    matchDataList.forEach((data) => {
        const { match, isGroup, otherUser, groupInfo, lastMessage } = data;

        const matchItem = document.createElement('div');
        matchItem.className = 'chat-item flex items-center px-5 py-4 cursor-pointer hover:bg-gray-50 transition-all duration-200';
        matchItem.setAttribute('data-match-id', match.id);

        if (!isGroup) {
            matchItem.setAttribute('data-user-id', otherUser.id);
        }

        // 時刻をフォーマット
        let timeString = '-';
        let previewText = isGroup ? 'グループチャットを開始' : 'チャットを開始';
        let displayName = isGroup ? groupInfo.name : (otherUser.handle || 'Unknown User');
        let avatarUrl = isGroup
            ? (groupInfo.avatar_url || 'https://placehold.co/48x48/f0f0f0/666?text=G')
            : (otherUser.avatar_url || 'https://placehold.co/48x48/f0f0f0/666?text=U');

        if (lastMessage) {
            const createdAt = new Date(lastMessage.created_at);
            const now = new Date();
            const diffMs = now - createdAt;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            if (diffMins < 1) {
                timeString = 'たった今';
            } else if (diffMins < 60) {
                timeString = `${diffMins}分前`;
            } else if (diffHours < 24) {
                timeString = `${diffHours}時間前`;
            } else if (diffDays < 7) {
                timeString = `${diffDays}日前`;
            } else {
                timeString = createdAt.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
            }

            previewText = lastMessage.body.length > 30
                ? lastMessage.body.substring(0, 30) + '...'
                : lastMessage.body;
        }

        const avatarHtml = !isGroup && otherUser
            ? `<a href="/profile.html?id=${otherUser.id}" class="relative flex-shrink-0" onclick="event.stopPropagation()">
                 <img src="${avatarUrl}" 
                      alt="${displayName}" 
                      class="w-14 h-14 rounded-full object-cover mr-4 border-2 border-gray-200"
                      onerror="this.onerror=null; this.src='https://placehold.co/48x48/f0f0f0/666?text=U'">
                 <div class="absolute bottom-0 right-3 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
               </a>`
            : `<div class="relative flex-shrink-0">
                 <img src="${avatarUrl}" 
                      alt="${displayName}" 
                      class="w-14 h-14 rounded-full object-cover mr-4 border-2 border-gray-200 ${isGroup ? 'group-avatar' : ''}"
                      onerror="this.onerror=null; this.src='https://placehold.co/48x48/f0f0f0/666?text=${isGroup ? 'G' : 'U'}'">
               </div>`;

        matchItem.innerHTML = `
            ${avatarHtml}
            <div class="flex-grow min-w-0">
                <div class="flex justify-between items-center mb-1">
                    <h2 class="text-sm font-semibold text-gray-900 truncate">${displayName}</h2>
                    <span class="text-xs text-gray-500 flex-shrink-0 ml-2" id="match-time-${match.id}">${timeString}</span>
                </div>
                <p class="text-xs text-gray-600 truncate" id="match-preview-${match.id}">${escapeHtml(previewText)}</p>
                ${isGroup ? '<p class="text-xs text-gray-400 mt-1">グループ</p>' : ''}
            </div>
        `;

        // クリックイベント
        matchItem.addEventListener('click', () => {
            if (isGroup) {
                selectGroupChat(match, groupInfo);
            } else {
                selectMatch(match, otherUser);
            }
        });

        container.appendChild(matchItem);
    });
}

/**
 * マッチを選択（ダイレクトチャット） (exportを追加)
 */
export async function selectMatch(match, otherUser) {
    // 既存のWebSocket接続を閉じる
    if (websocket) {
        websocket.close();
        websocket = null;
    }

    currentMatchId = match.id;
    currentOtherUserId = otherUser.id;
    currentPartnerName = otherUser.handle || 'Unknown User';

    // アクティブなマッチのハイライトを更新
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active-chat', 'bg-gray-100');
    });
    const selectedItem = document.querySelector(`[data-match-id="${match.id}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active-chat', 'bg-gray-100');
    }

    // チャットヘッダーを更新
    const chatHeader = document.getElementById('chat-header-content');
    const chatHeaderActions = document.getElementById('chat-header-actions');
    const chatHeaderStatus = document.getElementById('chat-header-status');
    chatHeader.innerHTML = `
        <div class="flex items-center space-x-3 flex-1 min-w-0">
            <a href="/profile.html?id=${otherUser.id}" class="flex-shrink-0 hover:opacity-80 transition-opacity">
                <img src="${otherUser.avatar_url || 'https://placehold.co/40x40/f0f0f0/666?text=U'}"
                     alt="${otherUser.handle}"
                     class="w-10 h-10 rounded-full object-cover border-2 border-gray-200 shadow-sm">
            </a>
            <div class="flex flex-col min-w-0 flex-1">
                <h2 class="text-lg font-semibold text-gray-800 truncate">${otherUser.handle || 'Unknown User'}</h2>
                <p class="text-xs text-gray-500 flex items-center">
                    <span class="w-2 h-2 bg-green-500 rounded-full mr-1.5"></span>
                    オンライン
                </p>
            </div>
        </div>
    `;
    chatHeaderActions.classList.remove('hidden');

    // アイコンを再初期化
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // モバイルの場合の表示切り替え
    if (window.innerWidth <= 767) {
        document.getElementById('chat-list').style.display = 'none';
        document.getElementById('chat-window').classList.add('active');
        document.getElementById('chat-window').style.display = 'flex';
    }

    // 会話履歴を取得
    const conversation = await fetchConversation(match.id);
    if (!conversation) {
        return;
    }

    currentConversationId = conversation.id;
    currentIsGroupChat = false;  // ダイレクトチャット

    // メッセージをレンダリング
    renderMessages(conversation.messages);

    // メッセージ入力エリアを表示
    document.getElementById('message-input-area').classList.remove('hidden');

    // WebSocket接続
    connectWebSocket(conversation.id, false);
}

/**
 * グループチャットを選択 (exportを追加)
 */
export async function selectGroupChat(match, groupInfo) {
    // 既存のWebSocket接続を閉じる
    if (websocket) {
        websocket.close();
        websocket = null;
    }

    currentMatchId = match.id;

    // アクティブなマッチのハイライトを更新
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active-chat', 'bg-gray-100');
    });
    const selectedItem = document.querySelector(`[data-match-id="${match.id}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active-chat', 'bg-gray-100');
    }

    // チャットヘッダーを更新
    const chatHeader = document.getElementById('chat-header-content');
    const chatHeaderActions = document.getElementById('chat-header-actions');
    chatHeader.innerHTML = `
        <div class="flex items-center space-x-3 flex-1 min-w-0">
            <img src="${groupInfo.avatar_url || 'https://placehold.co/40x40/f0f0f0/666?text=G'}" 
                 alt="${groupInfo.name}" 
                 class="w-10 h-10 rounded-full object-cover border-2 border-gray-200 flex-shrink-0 shadow-sm"
                 onerror="this.onerror=null; this.src='https://placehold.co/40x40/f0f0f0/666?text=G'">
            <div class="flex flex-col min-w-0 flex-1">
                <h2 class="text-lg font-semibold text-gray-800 truncate">${groupInfo.name}</h2>
                <p class="text-xs text-gray-500">グループ • ${groupInfo.member_count || 0} メンバー</p>
            </div>
        </div>
    `;
    chatHeaderActions.classList.remove('hidden');

    // アイコンを再初期化
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // モバイルの場合の表示切り替え
    if (window.innerWidth <= 767) {
        document.getElementById('chat-list').style.display = 'none';
        document.getElementById('chat-window').classList.add('active');
        document.getElementById('chat-window').style.display = 'flex';
    }

    // 会話履歴を取得（グループチャット）
    const conversation = await fetchConversation(match.id, true);
    if (!conversation) {
        return;
    }

    currentConversationId = conversation.id;
    currentIsGroupChat = true;  // グループチャット

    // メッセージをレンダリング
    renderMessages(conversation.messages);

    // メッセージ入力エリアを表示
    document.getElementById('message-input-area').classList.remove('hidden');

    // WebSocket接続
    connectWebSocket(conversation.id, true);
}

/**
 * メッセージをレンダリング
 */
function renderMessages(messages) {
    const messagesArea = document.getElementById('messages-area');
    messagesArea.innerHTML = '';

    if (messages.length === 0) {
        messagesArea.innerHTML = '<div class="flex items-center justify-center h-full text-gray-400"><p>メッセージがありません</p></div>';
        return;
    }

    messages.forEach(message => {
        const isOwnMessage = message.sender_id === currentUser.id;
        appendMessage(message, isOwnMessage);
    });

    // アイコンを初期化
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // スクロールを最下部に
    setTimeout(() => {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }, 100);
}

/**
 * メッセージを追加
 */
async function appendMessage(message, isOwnMessage = null) {
    if (isOwnMessage === null) {
        isOwnMessage = message.sender_id === currentUser.id;
    }

    const messagesArea = document.getElementById('messages-area');
    const emptyMessage = messagesArea.querySelector('.flex.items-center.justify-center');
    if (emptyMessage) {
        emptyMessage.remove();
    }

    // 送信者の情報を取得（キャッシュから取得、なければ取得）
    let senderInfo = null;
    if (!isOwnMessage) {
        senderInfo = userCache[message.sender_id] || await getUserInfo(message.sender_id);
    }

    // 時刻をフォーマット
    const createdAt = new Date(message.created_at);
    const timeString = createdAt.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', hour12: false });

    const messageHtml = isOwnMessage
        ? `
        <div class="flex justify-end mb-4 group" data-message-id="${message.id}">
            <div class="max-w-sm md:max-w-md lg:max-w-lg xl:max-w-2xl flex flex-col items-end">
                <div class="message-bubble user text-sm text-white shadow-lg">${escapeHtml(message.body)}</div><span class="text-xs text-gray-500 mt-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity">${timeString}</span>
            </div>
        </div>
        `
        : `
        <div class="flex justify-start mb-4 group" data-message-id="${message.id}">
            <a href="/profile.html?id=${senderInfo?.id}" class="flex-shrink-0 mr-3 hover:opacity-80 transition-opacity">
                <img src="${senderInfo?.avatar_url || 'https://placehold.co/32x32/f0f0f0/666?text=U'}" 
                     alt="${senderInfo?.handle || 'Unknown'}" 
                     class="w-10 h-10 rounded-full object-cover border-2 border-gray-200 shadow-sm"
                     onerror="this.onerror=null; this.src='https://placehold.co/32x32/f0f0f0/666?text=U'">
            </a>
            <div class="max-w-sm md:max-w-md lg:max-w-lg xl:max-w-2xl flex flex-col">
                <a href="/profile.html?id=${senderInfo?.id}" class="text-xs font-semibold text-gray-700 mb-1.5 hover:underline">${senderInfo?.handle || 'Unknown User'}</a>
                <div class="message-bubble other text-sm text-gray-900 shadow-md">${escapeHtml(message.body)}</div><span class="text-xs text-gray-500 mt-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity">${timeString}</span>
            </div>
        </div>
        `;

    messagesArea.insertAdjacentHTML('beforeend', messageHtml);

    // アイコンを再初期化
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // スクロールを最下部に
    setTimeout(() => {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }, 50);

    // マッチリストのプレビューを更新
    if (currentMatchId) {
        updateMatchPreview(currentMatchId, message);
    }
}

/**
 * マッチリストのプレビューを更新
 */
function updateMatchPreview(matchId, message) {
    const previewElement = document.getElementById(`match-preview-${matchId}`);
    const timeElement = document.getElementById(`match-time-${matchId}`);

    if (previewElement) {
        const previewText = message.body.length > 30
            ? message.body.substring(0, 30) + '...'
            : message.body;
        previewElement.textContent = previewText;
    }

    if (timeElement) {
        const createdAt = new Date(message.created_at);
        const now = new Date();
        const diffMs = now - createdAt;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        let timeString = 'たった今';
        if (diffMins >= 1 && diffMins < 60) {
            timeString = `${diffMins}分前`;
        } else if (diffHours < 24) {
            timeString = `${diffHours}時間前`;
        } else if (diffDays < 7) {
            timeString = `${diffDays}日前`;
        } else {
            timeString = createdAt.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
        }

        timeElement.textContent = timeString;
    }
}

/**
 * HTMLエスケープ
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * WebSocket接続
 * @param {string} conversationId - 会話ID
 * @param {boolean} isGroupChat - グループチャットの場合true
 */
function connectWebSocket(conversationId, isGroupChat = false) {
    const token = getAuthToken();
    if (!token) {
        console.error('認証トークンがありません');
        return;
    }

    // グループチャットとダイレクトチャットで異なるエンドポイントとパラメータを使用
    let wsUrl;
    if (isGroupChat) {
        wsUrl = `${WS_BASE_URL}/group-chat?group_conversation_id=${conversationId}&token=${encodeURIComponent(token)}`;
    } else {
        wsUrl = `${WS_BASE_URL}/chat?conversation_id=${conversationId}&token=${encodeURIComponent(token)}`;
    }

    try {
        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            console.log('WebSocket接続が開きました');
            sendPing();
        };

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'message') {
                appendMessage(data);
            } else if (data.type === 'pong') {
                console.log('Pongを受信しました');
            } else if (data.type === 'error') {
                console.error('WebSocketエラー:', data.message);
                showError(data.message);
            }
            // WebRTCシグナリングメッセージの処理
            else if (['offer', 'answer', 'ice-candidate', 'reject', 'end'].includes(data.type)) {
                webrtcManager.handleSignalingMessage(data);
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocketエラー:', error);
            showError('WebSocket接続エラーが発生しました。');
        };

        websocket.onclose = () => {
            console.log('WebSocket接続が閉じました');
            if (currentConversationId) {
                setTimeout(() => {
                    if (currentConversationId === conversationId) {
                        connectWebSocket(conversationId, currentIsGroupChat);
                    }
                }, 3000);
            }
        };
    } catch (error) {
        console.error('WebSocket接続エラー:', error);
        showError('WebSocket接続に失敗しました。');
    }
}

/**
 * Pingを送信
 */
function sendPing() {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: 'ping' }));
    }
}

/**
 * メッセージを送信
 */
function sendMessage(messageText) {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        showError('WebSocket接続が確立されていません。');
        return;
    }

    if (!messageText.trim()) {
        return;
    }

    try {
        websocket.send(JSON.stringify({
            type: 'message',
            body: messageText.trim()
        }));
    } catch (error) {
        console.error('メッセージ送信エラー:', error);
        showError('メッセージの送信に失敗しました。');
    }
}

/**
 * エラーを表示 (exportを削除し、グローバル定義に委ねる)
 */
function showError(message) {
    const errorDiv = document.getElementById('chat-list-error');
    if (errorDiv) {
        errorDiv.innerHTML = `<p>${message}</p>`;
        errorDiv.classList.remove('hidden');
    }
    console.error(message);
}

/**
 * モバイル用戻るボタンの処理
 */
function handleBackToList() {
    if (window.innerWidth <= 767) {
        document.getElementById('chat-window').classList.remove('active');
        document.getElementById('chat-list').style.display = 'flex';
        document.getElementById('chat-window').style.display = 'none';
    }
}

// ---------------------------------------------------------------------
// 以下のDOM操作/ロジック関数は削除または外部ファイルへ移動:
// displayUserSearchResults, renderSelectedMembers, initChatCreationModal
// ---------------------------------------------------------------------


/**
 * 通話ボタンの初期化 (exportを追加)
 */
export function initCallButtons() {
    // ヘッダーの音声通話ボタン
    const audioCallButtons = document.querySelectorAll('[data-lucide="phone"]');
    audioCallButtons.forEach(button => {
        // 親要素がボタンの場合のみイベントを追加
        const parentButton = button.closest('button');
        if (parentButton && parentButton.id !== 'accept-call' && parentButton.id !== 'reject-call') {
            parentButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                startAudioCall();
            });
        }
    });

    // ヘッダーのビデオ通話ボタン
    const videoCallButtons = document.querySelectorAll('[data-lucide="video"]');
    videoCallButtons.forEach(button => {
        // 親要素がボタンの場合のみイベントを追加
        const parentButton = button.closest('button');
        if (parentButton && parentButton.id !== 'toggle-video') {
            parentButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                startVideoCall();
            });
        }
    });

    console.log('通話ボタンの初期化が完了しました');
}

/**
 * 音声通話を開始
 */
function startAudioCall() {
    if (!currentConversationId || !currentOtherUserId || !currentPartnerName) {
        alert('チャットを選択してください。');
        return;
    }

    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        alert('チャット接続が確立されていません。');
        return;
    }

    console.log('音声通話を開始:', {
        conversationId: currentConversationId,
        partnerId: currentOtherUserId,
        partnerName: currentPartnerName
    });

    webrtcManager.startCall(
        currentConversationId,
        currentOtherUserId,
        currentPartnerName,
        false, // 音声のみ
        websocket
    );
}

/**
 * ビデオ通話を開始
 */
function startVideoCall() {
    if (!currentConversationId || !currentOtherUserId || !currentPartnerName) {
        alert('チャットを選択してください。');
        return;
    }

    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        alert('チャット接続が確立されていません。');
        return;
    }

    console.log('ビデオ通話を開始:', {
        conversationId: currentConversationId,
        partnerId: currentOtherUserId,
        partnerName: currentPartnerName
    });

    webrtcManager.startCall(
        currentConversationId,
        currentOtherUserId,
        currentPartnerName,
        true, // ビデオあり
        websocket
    );
}

/**
 * 初期化 (exportを追加)
 */
export async function init() {
    // 現在のユーザー情報を取得
    currentUser = await getCurrentUser();
    if (!currentUser) {
        return;
    }

    // マッチ一覧を取得
    matches = await fetchMatches();

    // マッチ一覧をレンダリング
    await renderMatchList(matches);

    // 以前ここに initChatCreationModal() があったが、外部ファイルに分離された

    // フォーム送信イベント
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = document.getElementById('message-input');
            const messageText = input.value;
            if (messageText.trim()) {
                sendMessage(messageText);
                input.value = '';
            }
        });
    }

    // 戻るボタンイベント
    const backButton = document.getElementById('back-to-list');
    if (backButton) {
        backButton.addEventListener('click', handleBackToList);
    }

    // レスポンシブ対応
    window.addEventListener('resize', () => {
        if (window.innerWidth > 767) {
            document.getElementById('chat-list').style.display = 'flex';
            document.getElementById('chat-window').classList.remove('active');
            document.getElementById('chat-window').style.display = 'flex';
        } else {
            if (!currentMatchId) {
                document.getElementById('chat-list').style.display = 'flex';
                document.getElementById('chat-window').style.display = 'none';
            }
        }
    });

    // 初回ロード時のモバイル対応
    if (window.innerWidth <= 767) {
        document.getElementById('chat-list').style.display = 'flex';
        document.getElementById('chat-window').style.display = 'none';
    }
}
