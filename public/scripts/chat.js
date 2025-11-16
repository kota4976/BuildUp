/**
 * チャット機能のJavaScript
 * APIとWebSocketに接続してリアルタイムチャットを実現
 */

// API設定
const API_HOST_PORT = 'localhost:8080';
const API_BASE_URL = `http://${API_HOST_PORT}/api/v1`;
// WebSocket URLも修正
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_BASE_URL = `${WS_PROTOCOL}//${API_HOST_PORT}/ws`;

// グローバル変数
let currentUser = null;
let currentMatchId = null;
let currentConversationId = null;
let websocket = null;
let matches = [];
let userCache = {}; // ユーザー情報のキャッシュ

/**
 * JWTトークンを取得
 */
function getAuthToken() {
    // ▼▼▼ [修正] 'auth_token' -> 'access_token' に変更 ▼▼▼
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
                // 認証エラーの場合、ログインページにリダイレクト
                // ▼▼▼ [修正] ログインページのパスを '/public/' に修正 ▼▼▼
                window.location.href = '/public/login.html';
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('現在のユーザー情報の取得に失敗しました:', error);
        // ▼▼▼ [修正] ログインページのパスを '/public/' に修正 ▼▼▼
        showError('認証に失敗しました。 <a href="/public/login.html">ログイン</a> してください。');
        return null;
    }
}

/**
 * ユーザー情報を取得（キャッシュ付き）
 */
async function getUserInfo(userId) {
    if (userCache[userId]) {
        return userCache[userId];
    }

    try {
        // ▼▼▼ [修正] バックエンドの /users/{id} API を呼び出す ▼▼▼
        const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
            // ▼▼▼ [追加] 認証ヘッダーを追加 ▼▼▼
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
        return {
            id: userId,
            handle: 'Unknown User',
            avatar_url: 'https://placehold.co/48x48/f0f0f0/666?text=U'
        };
    }
}

/**
 * マッチ一覧を取得
 */
async function fetchMatches() {
    try {
        const token = getAuthToken();
        if (!token) {
            throw new Error('認証トークンがありません');
        }

        const response = await fetch(`${API_BASE_URL}/matches/me/matches`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // ▼▼▼ [修正] ログインページのパスを '/public/' に修正 ▼▼▼
                window.location.href = '/public/login.html';
                return [];
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.matches || [];
    } catch (error) {
        console.error('マッチ一覧の取得に失敗しました:', error);
        showError('マッチ一覧の取得に失敗しました。');
        return [];
    }
}

/**
 * 会話履歴を取得
 */
async function fetchConversation(matchId) {
    try {
        const token = getAuthToken();
        if (!token) {
            throw new Error('認証トークンがありません');
        }

        const response = await fetch(`${API_BASE_URL}/matches/${matchId}/conversation?limit=50`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // ▼▼▼ [修正] ログインページのパスを '/public/' に修正 ▼▼▼
                window.location.href = '/public/login.html';
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('会話履歴の取得に失敗しました:', error);
        showError('会話履歴の取得に失敗しました。');
        return null;
    }
}

/**
 * マッチ一覧をレンダリング
 */
async function renderMatchList(matches) {
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
            // 相手のユーザーIDを取得
            const otherUserId = match.user_a === currentUser.id ? match.user_b : match.user_a;

            // ユーザー情報を取得
            const otherUser = await getUserInfo(otherUserId);

            // 会話履歴を取得（最新1件のみ）
            let lastMessage = null;
            try {
                const conversation = await fetchConversation(match.id);
                if (conversation && conversation.messages && conversation.messages.length > 0) {
                    lastMessage = conversation.messages[conversation.messages.length - 1];
                }
            } catch (error) {
                console.warn(`会話履歴の取得に失敗しました (match_id: ${match.id}):`, error);
            }

            return { match, otherUser, lastMessage };
        } catch (error) {
            console.error(`マッチ情報の取得に失敗しました (match_id: ${match.id}):`, error);
            const otherUserId = match.user_a === currentUser.id ? match.user_b : match.user_a;
            return {
                match,
                otherUser: {
                    id: otherUserId,
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
    matchDataList.forEach(({ match, otherUser, lastMessage }) => {
        const matchItem = document.createElement('div');
        matchItem.className = 'chat-item flex items-center px-5 py-4 cursor-pointer hover:bg-gray-50 transition-all duration-200';
        matchItem.setAttribute('data-match-id', match.id);
        matchItem.setAttribute('data-user-id', otherUser.id);

        // 時刻をフォーマット
        let timeString = '-';
        let previewText = 'チャットを開始';
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

        matchItem.innerHTML = `
            <div class="relative flex-shrink-0">
                <img src="${otherUser.avatar_url || 'https://placehold.co/48x48/f0f0f0/666?text=U'}" 
                     alt="${otherUser.handle}" 
                     class="w-14 h-14 rounded-full object-cover mr-4 border-2 border-gray-200"
                     onerror="this.onerror=null; this.src='https://placehold.co/48x48/f0f0f0/666?text=U'">
                <div class="absolute bottom-0 right-3 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
            </div>
            <div class="flex-grow min-w-0">
                <div class="flex justify-between items-center mb-1">
                    <h2 class="text-sm font-semibold text-gray-900 truncate">${otherUser.handle || 'Unknown User'}</h2>
                    <span class="text-xs text-gray-500 flex-shrink-0 ml-2" id="match-time-${match.id}">${timeString}</span>
                </div>
                <p class="text-xs text-gray-600 truncate" id="match-preview-${match.id}">${escapeHtml(previewText)}</p>
            </div>
        `;

        // クリックイベント
        matchItem.addEventListener('click', () => {
            selectMatch(match, otherUser);
        });

        container.appendChild(matchItem);
    });
}

/**
 * マッチを選択
 */
async function selectMatch(match, otherUser) {
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
    const chatHeaderStatus = document.getElementById('chat-header-status');
    chatHeader.innerHTML = `
        <div class="flex items-center space-x-3 flex-1 min-w-0">
            <img src="${otherUser.avatar_url || 'https://placehold.co/40x40/f0f0f0/666?text=U'}" 
                 alt="${otherUser.handle}" 
                 class="w-10 h-10 rounded-full object-cover border-2 border-gray-200 flex-shrink-0 shadow-sm"
                 onerror="this.onerror=null; this.src='https://placehold.co/40x40/f0f0f0/666?text=U'">
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

    // メッセージをレンダリング
    renderMessages(conversation.messages);

    // メッセージ入力エリアを表示
    document.getElementById('message-input-area').classList.remove('hidden');

    // WebSocket接続
    connectWebSocket(conversation.id);
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
            <div class="max-w-xs md:max-w-md lg:max-w-lg flex flex-col items-end">
                <div class="message-bubble user text-sm text-white shadow-lg">
                    ${escapeHtml(message.body)}
                </div>
                <span class="text-xs text-gray-500 mt-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity">${timeString}</span>
            </div>
        </div>
        `
        : `
        <div class="flex justify-start mb-4 group" data-message-id="${message.id}">
            <img src="${senderInfo?.avatar_url || 'https://placehold.co/32x32/f0f0f0/666?text=U'}" 
                 alt="${senderInfo?.handle || 'Unknown'}" 
                 class="w-10 h-10 rounded-full object-cover mr-3 flex-shrink-0 border-2 border-gray-200 shadow-sm"
                 onerror="this.onerror=null; this.src='https://placehold.co/32x32/f0f0f0/666?text=U'">
            <div class="max-w-xs md:max-w-md lg:max-w-lg flex flex-col">
                <p class="text-xs font-semibold text-gray-700 mb-1.5">${senderInfo?.handle || 'Unknown User'}</p>
                <div class="message-bubble other text-sm text-gray-900 shadow-md">
                    ${escapeHtml(message.body)}
                </div>
                <span class="text-xs text-gray-500 mt-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity">${timeString}</span>
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
 */
function connectWebSocket(conversationId) {
    const token = getAuthToken();
    if (!token) {
        console.error('認証トークンがありません');
        return;
    }

    // WebSocket URLを構築
    const wsUrl = `${WS_BASE_URL}/chat?conversation_id=${conversationId}&token=${encodeURIComponent(token)}`;

    try {
        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            console.log('WebSocket接続が開きました');
            // 接続確認のためpingを送信
            sendPing();
        };

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'message') {
                // メッセージを受信
                appendMessage(data);
            } else if (data.type === 'pong') {
                // Pongを受信（接続確認）
                console.log('Pongを受信しました');
            } else if (data.type === 'error') {
                console.error('WebSocketエラー:', data.message);
                showError(data.message);
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocketエラー:', error);
            showError('WebSocket接続エラーが発生しました。');
        };

        websocket.onclose = () => {
            console.log('WebSocket接続が閉じました');
            // 再接続を試みる（3秒後）
            if (currentConversationId) {
                setTimeout(() => {
                    if (currentConversationId === conversationId) {
                        connectWebSocket(conversationId);
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
 * エラーを表示
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

/**
 * 初期化
 */
async function init() {

    // ▼▼▼ [削除] ログイン直後のトークン処理 (不要なため) ▼▼▼
    // const hash = window.location.hash.substring(1);
    // ... (中略) ...
    // history.replaceState(null, '', window.location.pathname + window.location.search);
    // ▲▲▲ トークン処理ここまで ▲▲▲

    // 現在のユーザー情報を取得
    currentUser = await getCurrentUser();
    if (!currentUser) {
        return; // getCurrentUser内でリダイレクト処理済み
    }

    // マッチ一覧を取得
    matches = await fetchMatches();

    // マッチ一覧をレンダリング
    await renderMatchList(matches);

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

// ページロード時に初期化
document.addEventListener('DOMContentLoaded', init);