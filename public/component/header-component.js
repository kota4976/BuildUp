// API設定
// FastAPIのポート (8080) を明示的に指定
const API_BASE_URL = 'http://localhost:8080/api/v1';

class BuildUpHeader extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.isLoggedIn = false;
        this.userHandle = null;
        this.userAvatar = null;

        // 初期のレイアウトHTMLを定義 (ロード中/未認証時のベース)
        this.baseTemplate = `
            <style>
                /* --- CSS: コンポーネントの見た目を定義 --- */
                :host {
                    display: block;
                    position: sticky;
                    top: 0;
                    z-index: 1000;
                }
                
                .navbar {
                    background-color: #ffffff;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* シャドウを少し強める */
                    display: flex; 
                    justify-content: center;
                    padding: 12px 40px; /* パディングを調整 */
                }

                .navbar-container {
                    max-width: 1200px;
                    width: 100%;
                    margin: 0 auto;
                    display: flex;
                    /* [修正] 左右寄せに変更 */
                    justify-content: space-between; 
                    align-items: center;
                }

                .nav-left {
                    display: flex;
                    align-items: center;
                }
                
                /* ロゴ */
                .logo { text-decoration: none; display: flex; align-items: center; }
                .logo-img { height: 35px; width: auto; display: block; }

                /* メニュー */
                .nav-menu {
                    margin-left: 40px;
                    display: flex;
                    gap: 30px;
                }
                .nav-link {
                    text-decoration: none;
                    color: #555;
                    font-weight: 500;
                    font-size: 0.95rem;
                    padding: 5px 0;
                    transition: all 0.2s ease; /* トランジション追加 */
                }
                .nav-link:hover {
                    color: #007bff;
                    border-bottom: 2px solid #007bff;
                }
                
                /* 右側ボタン */
                .nav-right-buttons {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .auth-button {
                    padding: 8px 15px;
                    border-radius: 6px;
                    font-size: 0.9rem;
                    font-weight: 600;
                    text-decoration: none;
                    transition: background-color 0.2s ease;
                }
                .login-btn {
                    background-color: #f0f0f0;
                    color: #333;
                }
                .login-btn:hover {
                    background-color: #e0e0e0;
                }
                .signup-btn {
                    background-color: #007bff;
                    color: white;
                }
                .signup-btn:hover {
                    background-color: #0056b3;
                }

                /* アバターアイコン */
                .profile-icon {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    object-fit: cover;
                    cursor: pointer;
                    border: 2px solid transparent;
                    transition: border-color 0.2s ease;
                }
                .profile-icon:hover {
                    border-color: #007bff;
                }
                
                /* --- レスポンシブ対応 --- */
                @media (max-width: 768px) {
                    .navbar {
                        padding: 10px 20px;
                    }
                    .nav-menu {
                        /* モバイルではメニューを非表示 */
                        display: none;
                    }
                    .auth-button {
                        padding: 6px 12px;
                    }
                    .profile-icon {
                        width: 36px;
                        height: 36px;
                    }
                    .menu-toggle {
                        display: block !important; 
                        margin-left: 10px;
                    }
                }
            </style>

            <header class="navbar">
                <div class="navbar-container">
                    <div class="nav-left">
                        <a href="/public/index.html" class="logo">
                            <img src="images/BuildUp-logo.jpg" alt="BuildUp Logo" class="logo-img">
                        </a>
                        <nav class="nav-menu">
                            <a href="/public/projectReserch.html" class="nav-link">プロジェクト</a>
                            <a href="/public/chat.html" class="nav-link">メッセージ</a>
                            <a href="/public/applications.html" class="nav-link">応募管理</a>
                        </nav>
                    </div>
                    
                    <!-- 認証状態に応じて中身が変わるコンテナ -->
                    <div id="auth-status-container" class="nav-right-buttons">
                        <!-- ロード中はスピナーか何も表示しない -->
                        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                    </div>
                </div>
            </header>
        `;
    }

    // コンポーネントがDOMに追加されたときに実行
    connectedCallback() {
        this.shadowRoot.innerHTML = this.baseTemplate;
        this.checkAuthStatus();
        this.addEventListeners();
    }

    // 認証状態の確認
    async checkAuthStatus() {
        const token = localStorage.getItem('access_token');
        const container = this.shadowRoot.getElementById('auth-status-container');

        if (!token) {
            this.isLoggedIn = false;
            this.renderUI(null);
            return;
        }

        try {
            // /auth/me を呼び出してトークンの有効性を確認
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                this.isLoggedIn = true;
                this.userHandle = userData.handle;
                this.userAvatar = userData.avatar_url;
                this.renderUI(userData);
            } else {
                // トークンが無効
                localStorage.removeItem('access_token');
                this.isLoggedIn = false;
                this.renderUI(null);
            }
        } catch (error) {
            // ネットワークエラーなど
            console.error('Header auth check failed:', error);
            this.isLoggedIn = false;
            this.renderUI(null);
        }
    }

    // 認証状態に応じてHTMLをレンダリング
    renderUI(userData) {
        const container = this.shadowRoot.getElementById('auth-status-container');
        container.innerHTML = '';

        if (userData && this.isLoggedIn) {
            // ログイン済み (アバターアイコン)
            container.innerHTML = `
                <a href="/public/profile.html">
                    <img src="${this.userAvatar || 'images/default-avatar.png'}" 
                         alt="${this.userHandle}" 
                         class="profile-icon"
                         onerror="this.onerror=null; this.src='images/default-avatar.png'">
                </a>
            `;
            // ログアウト機能（アイコンクリックでメニュー表示などを想定）

        } else {
            // 未ログイン (Login/Sign Up ボタン)
            container.innerHTML = `
                <a href="/public/login.html" class="auth-button login-btn">ログイン</a>
                <a href="/public/signup.html" class="auth-button signup-btn">サインアップ</a>
            `;
        }
    }

    // イベントリスナーの追加
    addEventListeners() {
        const container = this.shadowRoot.querySelector('.navbar-container');
        // 将来的な拡張のため
    }
}

// カスタム要素として登録
customElements.define('build-up-header', BuildUpHeader);