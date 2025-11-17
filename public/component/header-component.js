// API設定
// nginx経由でアクセスするため相対パスを使用
const API_BASE_URL = "/api/v1";

class BuildUpHeader extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
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
                
                /* ドロップダウンメニュー */
                .profile-dropdown {
                    position: relative;
                }
                .dropdown-menu {
                    display: none;
                    position: absolute;
                    top: 50px;
                    right: 0;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    min-width: 180px;
                    z-index: 1000;
                }
                .dropdown-menu.show {
                    display: block;
                }
                .dropdown-item {
                    padding: 12px 16px;
                    text-decoration: none;
                    color: #333;
                    display: block;
                    transition: background-color 0.2s;
                }
                .dropdown-item:hover {
                    background-color: #f5f5f5;
                }
                .dropdown-divider {
                    height: 1px;
                    background-color: #e0e0e0;
                    margin: 4px 0;
                }
                .logout-btn {
                    color: #dc3545;
                    cursor: pointer;
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
                        <a href="/" class="logo">
                            <img src="images/BuildUp-logo.jpg" alt="BuildUp Logo" class="logo-img">
                        </a>
                        <nav class="nav-menu">
                            <a href="/projectReserch.html" class="nav-link">プロジェクト</a>
                            <a href="/chat.html" class="nav-link">メッセージ</a>
                            <a href="/applications.html" class="nav-link">応募管理</a>
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
    const token = localStorage.getItem("access_token");
    const container = this.shadowRoot.getElementById("auth-status-container");

    if (!token) {
      this.isLoggedIn = false;
      this.renderUI(null);
      return;
    }

    try {
      // /auth/me を呼び出してトークンの有効性を確認
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        this.isLoggedIn = true;
        this.userHandle = userData.handle;
        this.userAvatar = userData.avatar_url;
        this.renderUI(userData);
      } else {
        // トークンが無効
        localStorage.removeItem("access_token");
        this.isLoggedIn = false;
        this.renderUI(null);
      }
    } catch (error) {
      // ネットワークエラーなど
      console.error("Header auth check failed:", error);
      this.isLoggedIn = false;
      this.renderUI(null);
    }
  }

  // 認証状態に応じてHTMLをレンダリング
  renderUI(userData) {
    const container = this.shadowRoot.getElementById("auth-status-container");
    container.innerHTML = "";

    if (userData && this.isLoggedIn) {
      // ログイン済み (アバターアイコンとドロップダウンメニュー)
      container.innerHTML = `
                <div class="profile-dropdown">
                    <img src="${
                      this.userAvatar || "images/default-avatar.png"
                    }" 
                         alt="${this.userHandle}" 
                         class="profile-icon"
                         id="profile-avatar-icon"
                         onerror="this.onerror=null; this.src='images/default-avatar.png'">
                    <div class="dropdown-menu" id="profile-dropdown-menu">
                        <a href="/profile.html" class="dropdown-item">
                            プロフィール
                        </a>
                        <div class="dropdown-divider"></div>
                        <a class="dropdown-item logout-btn" id="logout-btn">
                            ログアウト
                        </a>
                    </div>
                </div>
            `;

      // ドロップダウンメニューのイベントリスナーを設定
      const avatarIcon = this.shadowRoot.getElementById("profile-avatar-icon");
      const dropdownMenu = this.shadowRoot.getElementById(
        "profile-dropdown-menu"
      );
      const logoutBtn = this.shadowRoot.getElementById("logout-btn");
      const profileLink = this.shadowRoot.querySelector(
        'a[href="/profile.html"]'
      );

      avatarIcon.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation(); // イベントの伝播を停止
        dropdownMenu.classList.toggle("show");
      });

      // プロフィールリンクのクリックイベント
      if (profileLink) {
        profileLink.addEventListener("click", (e) => {
          e.preventDefault();
          e.stopPropagation(); // イベントの伝播を停止
          dropdownMenu.classList.remove("show"); // ドロップダウンを閉じる
          window.location.href = "/profile.html";
        });
      }

      // ドロップダウン外をクリックしたら閉じる
      // composedPath() を使用して Shadow DOM 内の要素も正しく検出
      document.addEventListener("click", (e) => {
        const path = e.composedPath();
        if (!path.includes(avatarIcon) && !path.includes(dropdownMenu)) {
          dropdownMenu.classList.remove("show");
        }
      });

      // ログアウトボタンのイベントリスナー
      logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation(); // イベントの伝播を停止
        this.handleLogout();
      });
    } else {
      // 未ログイン (Login/Sign Up ボタン)
      container.innerHTML = `
                <a href="/login.html" class="auth-button login-btn">ログイン</a>
                <a href="/signup.html" class="auth-button signup-btn">サインアップ</a>
            `;
    }
  }

  // イベントリスナーの追加
  addEventListeners() {
    // localStorage の変更を監視（他のタブや同じページ内での変更を検知）
    window.addEventListener("storage", (e) => {
      if (e.key === "access_token") {
        console.log("Header: localStorage の access_token が変更されました");
        this.checkAuthStatus();
      }
    });

    // カスタムイベントを監視（同じページ内でのトークン保存を検知）
    window.addEventListener("auth-state-changed", () => {
      console.log("Header: auth-state-changed イベントを受信しました");
      this.checkAuthStatus();
    });
  }

  // 外部から認証状態を更新するためのメソッド
  refresh() {
    console.log("Header: refresh() が呼ばれました");
    this.checkAuthStatus();
  }

  // ログアウト処理
  handleLogout() {
    console.log("Header: ログアウト処理を開始します");

    // localStorageからトークンを削除
    localStorage.removeItem("access_token");

    // 状態をリセット
    this.isLoggedIn = false;
    this.userHandle = null;
    this.userAvatar = null;

    // UIを更新
    this.renderUI(null);

    // 認証状態変更イベントを発火
    window.dispatchEvent(new Event("auth-state-changed"));

    // ログインページにリダイレクト
    window.location.href = "/login.html";
  }
}

// カスタム要素として登録
customElements.define("build-up-header", BuildUpHeader);
