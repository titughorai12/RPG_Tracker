// ============================================================
// RPG TRACKER - SCRIPT.JS
// Complete clean replacement
// ============================================================

const API_URL = "";

// ============================================================
// API FUNCTION
// ============================================================

async function apiFetch(endpoint, options = {}) {
    const config = {
        method: options.method || "GET",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (options.body !== undefined) {
        config.body = options.body;
    }

    const response = await fetch(API_URL + endpoint, config);

    let data = {};

    try {
        data = await response.json();
    } catch (error) {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.error ||
            data.message ||
            `Request failed: ${response.status}`
        );
    }

    return data;
}

// ============================================================
// PAGE LOAD
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("================================");
    console.log("RPG TRACKER STARTED");
    console.log("================================");

    // Register page
    if (document.getElementById("registerForm")) {
        initializeRegister();
    }

    // Login page
    if (document.getElementById("loginForm")) {
        initializeLogin();
    }

    // Dashboard page
    if (
        document.getElementById("taskForm") ||
        document.getElementById("taskList")
    ) {
        initializeDashboard();
    }
});

// ============================================================
// REGISTER
// ============================================================

function initializeRegister() {

    const form = document.getElementById("registerForm");

    if (!form) {
        return;
    }

    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        const username =
            document.getElementById("registerUsername")?.value.trim();

        const email =
            document.getElementById("registerEmail")?.value.trim();

        const password =
            document.getElementById("registerPassword")?.value;

        const message =
            document.getElementById("registerMessage");

        const button =
            document.getElementById("registerButton");

        if (!username || !email || !password) {

            showMessage(
                message,
                "Please fill all fields.",
                "error"
            );

            return;
        }

        if (password.length < 6) {

            showMessage(
                message,
                "Password must be at least 6 characters.",
                "error"
            );

            return;
        }

        if (button) {
            button.disabled = true;
            button.innerText = "Creating Account...";
        }

        try {

            const result = await apiFetch("/api/register", {
                method: "POST",
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });

            console.log("Registration successful:", result);

            showMessage(
                message,
                "Account created successfully!",
                "success"
            );

            setTimeout(function () {
                window.location.href = "/login.html";
            }, 1000);

        } catch (error) {

            console.error("Registration error:", error);

            showMessage(
                message,
                error.message,
                "error"
            );

            if (button) {
                button.disabled = false;
                button.innerText = "Create Account";
            }
        }
    });
}

// ============================================================
// LOGIN
// ============================================================

function initializeLogin() {

    const form = document.getElementById("loginForm");

    if (!form) {
        return;
    }

    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        const username =
            document.getElementById("loginUsername")?.value.trim();

        const password =
            document.getElementById("loginPassword")?.value;

        const message =
            document.getElementById("loginMessage");

        const button =
            document.getElementById("loginButton");

        if (!username || !password) {

            showMessage(
                message,
                "Please enter username and password.",
                "error"
            );

            return;
        }

        if (button) {
            button.disabled = true;
            button.innerText = "Logging in...";
        }

        try {

            const result = await apiFetch("/api/login", {
                method: "POST",
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            console.log("Login successful:", result);

            showMessage(
                message,
                "Login successful!",
                "success"
            );

            setTimeout(function () {
                window.location.href = "/dashboard.html";
            }, 700);

        } catch (error) {

            console.error("Login error:", error);

            showMessage(
                message,
                error.message,
                "error"
            );

            if (button) {
                button.disabled = false;
                button.innerText = "Login";
            }
        }
    });
}

// ============================================================
// DASHBOARD INITIALIZATION
// ============================================================

async function initializeDashboard() {

    console.log("Initializing dashboard...");

    initializeTaskForm();

    try {

        const me = await apiFetch("/api/me");

        console.log("Current user:", me);

        if (!me.user) {

            window.location.href = "/login.html";

            return;
        }

        window.currentUser = me.user;

        await refreshDashboard();

    } catch (error) {

        console.error(
            "Dashboard initialization error:",
            error
        );
    }
}

// ============================================================
// REFRESH EVERYTHING
// ============================================================

async function refreshDashboard() {

    console.log("Refreshing dashboard...");

    try {

        await loadDashboard();
        await loadTasks();
        await loadShop();
        await loadInventory();

        console.log("Dashboard refresh complete.");

    } catch (error) {

        console.error(
            "Dashboard refresh error:",
            error
        );
    }
}

// ============================================================
// LOAD DASHBOARD DATA
// ============================================================

async function loadDashboard() {

    try {

        const data = await apiFetch("/api/dashboard");

        console.log("DATABASE DATA:", data);

        const user = data.user || {};
        const attributes = data.attributes || {};

        window.currentUser = user;

        // ====================================================
        // USERNAME
        // ====================================================

        setText(
            "username",
            user.username || "Player"
        );

        setText(
            "welcomeUsername",
            user.username || "Player"
        );

        setText(
            "navUsername",
            user.username || "Player"
        );

        // ====================================================
        // LEVEL
        // ====================================================

        const level = Number(user.level ?? 1);

        setText("level", level);
        setText("playerLevel", level);
        setText("navLevel", level);

        // ====================================================
        // XP
        // ====================================================

        const xp = Number(user.xp ?? 0);

        console.log("XP FROM DATABASE:", xp);

        setText("totalXP", xp);
        setText("playerXP", xp);
        setText("xpText", xp);

        // ====================================================
        // COINS
        // ====================================================

        /*
         * IMPORTANT:
         *
         * Dashboard has two main coin elements:
         *
         * Top:
         * id="navCoins"
         *
         * Middle:
         * id="totalCoins"
         *
         * Both MUST use the same database value.
         */

        const coins = Number(
            user.coins ??
            data.coins ??
            0
        );

        console.log("================================");
        console.log("COINS FROM DATABASE:", coins);
        console.log("================================");

        // TOP COINS
        setText("navCoins", coins);

        // MIDDLE COINS
        setText("totalCoins", coins);

        // Other possible coin elements
        setText("coins", coins);
        setText("playerCoins", coins);
        setText("coinBalance", coins);
        setText("coinAmount", coins);
        setText("currentCoins", coins);

        // ====================================================
        // STREAK
        // ====================================================

        const currentStreak = Number(
            user.current_streak ??
            user.streak ??
            0
        );

        const longestStreak = Number(
            user.longest_streak ??
            0
        );

        setText(
            "currentStreak",
            currentStreak
        );

        setText(
            "streak",
            currentStreak
        );

        setText(
            "longestStreak",
            longestStreak
        );

        // ====================================================
        // TASK STATISTICS
        // ====================================================

        if (data.stats) {

            setText(
                "totalQuests",
                data.stats.total_tasks ?? 0
            );

            setText(
                "completedQuests",
                data.stats.completed_tasks ?? 0
            );
        }

        // ====================================================
        // ATTRIBUTES
        // ====================================================

        setText(
            "strength",
            attributes.strength ?? 1
        );

        setText(
            "intelligence",
            attributes.intelligence ?? 1
        );

        setText(
            "discipline",
            attributes.discipline ?? 1
        );

        setText(
            "creativity",
            attributes.creativity ?? 1
        );

        setText(
            "social",
            attributes.social ?? 1
        );

        // ====================================================
        // XP BAR
        // ====================================================

        updateXPBar(user);

        // ====================================================
        // XP TEXT
        // ====================================================

        updateXPText(user);

    } catch (error) {

        console.error(
            "loadDashboard error:",
            error
        );
    }
}

// ============================================================
// XP BAR
// ============================================================

function updateXPBar(user) {

    let level = Number(user.level ?? 1);
    let xp = Number(user.xp ?? 0);

    let remainingXP = xp;

    while (
        remainingXP >= level * level * 100
    ) {

        remainingXP -= level * level * 100;

        level++;
    }

    const requiredXP =
        level * level * 100;

    const percentage =
        Math.min(
            100,
            (remainingXP / requiredXP) * 100
        );

    const progress =
        document.getElementById("xpProgress");

    if (progress) {

        progress.style.width =
            percentage + "%";
    }
}

// ============================================================
// XP TEXT
// ============================================================

function updateXPText(user) {

    let level = Number(user.level ?? 1);
    let xp = Number(user.xp ?? 0);

    let remainingXP = xp;

    while (
        remainingXP >= level * level * 100
    ) {

        remainingXP -= level * level * 100;

        level++;
    }

    const requiredXP =
        level * level * 100;

    setText(
        "xpProgressText",
        `${remainingXP} / ${requiredXP} XP`
    );
}

// ============================================================
// LOAD TASKS
// ============================================================

async function loadTasks() {

    try {

        const data =
            await apiFetch("/api/tasks");

        console.log("TASKS:", data);

        const tasks =
            Array.isArray(data)
                ? data
                : (data.tasks || []);

        renderTasks(tasks);

    } catch (error) {

        console.error(
            "loadTasks error:",
            error
        );
    }
}

// ============================================================
// RENDER TASKS
// ============================================================

function renderTasks(tasks) {

    const container =
        document.getElementById("taskList");

    if (!container) {

        console.error(
            "taskList not found."
        );

        return;
    }

    container.innerHTML = "";

    // ========================================================
    // NO QUESTS
    // ========================================================

    if (!tasks || tasks.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚔️</div>

                <h3>No quests yet</h3>

                <p>
                    Create your first real-life quest
                    and begin your adventure.
                </p>

                <button
                    type="button"
                    onclick="openTaskModal()"
                >
                    Create First Quest
                </button>
            </div>
        `;

        return;
    }

    // ========================================================
    // QUEST CARDS
    // ========================================================

    tasks.forEach(function (task) {

        const card =
            document.createElement("div");

        card.className = "quest-card";

        if (task.completed) {

            card.classList.add("completed");
        }

        const category =
            task.category || "General";

        const title =
            escapeHTML(task.title);

        const description =
            escapeHTML(
                task.description || ""
            );

        const xp =
            Number(task.xp_reward ?? 0);

        const coins =
            Number(task.coin_reward ?? 0);

        let actionHTML = "";

        if (task.completed) {

            actionHTML = `
                <button
                    class="complete-btn completed-btn"
                    disabled
                >
                    ✓ Completed
                </button>
            `;

        } else {

            actionHTML = `
                <button
                    class="complete-btn"
                    onclick="completeTask(${Number(task.id)})"
                >
                    Complete Quest
                </button>
            `;
        }

        card.innerHTML = `
            <div class="quest-category">
                ${escapeHTML(category)}
            </div>

            <h3>
                ${title}
            </h3>

            <p>
                ${description}
            </p>

            <div class="quest-rewards">
                <span>⭐ ${xp} XP</span>
                <span>🪙 ${coins}</span>
            </div>

            ${actionHTML}
        `;

        container.appendChild(card);
    });
}

// ============================================================
// OPEN QUEST MODAL
// ============================================================

function openTaskModal() {

    console.log(
        "Opening quest modal..."
    );

    const modal =
        document.getElementById("taskModal");

    if (!modal) {

        alert(
            "Quest modal not found."
        );

        return;
    }

    modal.style.display = "flex";

    modal.classList.add("active");

    const title =
        document.getElementById("taskTitle");

    if (title) {

        setTimeout(function () {

            title.focus();

        }, 100);
    }
}

// ============================================================
// CLOSE QUEST MODAL
// ============================================================

function closeTaskModal() {

    const modal =
        document.getElementById("taskModal");

    if (!modal) {
        return;
    }

    modal.style.display = "none";

    modal.classList.remove("active");
}

// ============================================================
// INITIALIZE QUEST FORM
// ============================================================

function initializeTaskForm() {

    const form =
        document.getElementById("taskForm");

    if (!form) {

        console.warn(
            "taskForm not found."
        );

        return;
    }

    if (
        form.dataset.initialized === "true"
    ) {

        return;
    }

    form.dataset.initialized = "true";

    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            console.log(
                "CREATE QUEST FORM SUBMITTED"
            );

            await createTask();
        }
    );
}

// ============================================================
// CREATE QUEST
// ============================================================

async function createTask() {

    console.log("================================");
    console.log("CREATING QUEST");
    console.log("================================");

    const title =
        document.getElementById("taskTitle")
            ?.value.trim();

    const description =
        document.getElementById("taskDescription")
            ?.value.trim() || "";

    const category =
        document.getElementById("taskCategory")
            ?.value || "General";

    const xpReward =
        Number(
            document.getElementById("taskXP")
                ?.value || 10
        );

    const coinReward =
        Number(
            document.getElementById("taskCoins")
                ?.value || 5
        );

    console.log("Title:", title);
    console.log("Description:", description);
    console.log("Category:", category);
    console.log("XP:", xpReward);
    console.log("Coins:", coinReward);

    if (!title) {

        alert(
            "Please enter a quest name."
        );

        return;
    }

    if (xpReward < 0 || coinReward < 0) {

        alert(
            "XP and coins cannot be negative."
        );

        return;
    }

    try {

        const result =
            await apiFetch("/api/tasks", {
                method: "POST",

                body: JSON.stringify({
                    title: title,
                    description: description,
                    category: category,
                    xp_reward: xpReward,
                    coin_reward: coinReward
                })
            });

        console.log(
            "QUEST CREATED:",
            result
        );

        // Reset form
        const form =
            document.getElementById("taskForm");

        if (form) {
            form.reset();
        }

        // Close modal
        closeTaskModal();

        // Reload database data
        await refreshDashboard();

        // Success popup
        showRewardPopup(
            "QUEST CREATED ⚔️",
            "Your new quest has been added!"
        );

    } catch (error) {

        console.error(
            "CREATE QUEST ERROR:",
            error
        );

        alert(
            "Could not create quest:\n\n" +
            error.message
        );
    }
}

// ============================================================
// COMPLETE QUEST
// ============================================================

async function completeTask(taskId) {

    console.log("================================");
    console.log(
        "COMPLETING QUEST:",
        taskId
    );
    console.log("================================");

    try {

        const result =
            await apiFetch(
                `/api/tasks/${taskId}/complete`,
                {
                    method: "POST"
                }
            );

        console.log(
            "QUEST COMPLETED:",
            result
        );

        // Reload PostgreSQL data
        await refreshDashboard();

        const xp =
            Number(
                result.xp_earned ??
                result.xp_reward ??
                0
            );

        const coins =
            Number(
                result.coins_earned ??
                result.coin_reward ??
                0
            );

        showRewardPopup(
            "QUEST COMPLETE! ⚔️",
            `+${xp} XP +${coins} 🪙`
        );

        if (
            result.level_up ||
            result.leveled_up
        ) {

            setTimeout(
                function () {

                    showRewardPopup(
                        "LEVEL UP! 🎉",
                        "Your character became stronger!"
                    );

                },
                1000
            );
        }

    } catch (error) {

        console.error(
            "COMPLETE QUEST ERROR:",
            error
        );

        alert(
            "Could not complete quest:\n\n" +
            error.message
        );
    }
}

// ============================================================
// SHOP
// ============================================================

async function loadShop() {

    try {

        const data =
            await apiFetch("/api/shop");

        console.log(
            "SHOP:",
            data
        );

        const items =
            Array.isArray(data)
                ? data
                : (data.items || []);

        renderShop(items);

    } catch (error) {

        console.error(
            "Shop error:",
            error
        );
    }
}

// ============================================================
// RENDER SHOP
// ============================================================

function renderShop(items) {

    const container =
        document.getElementById("shopList");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!items || items.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🛒</div>

                <h3>Shop is empty</h3>

                <p>
                    More rewards will appear here soon.
                </p>
            </div>
        `;

        return;
    }

    items.forEach(function (item) {

        const card =
            document.createElement("div");

        card.className = "shop-item";

        const itemId =
            Number(
                item.id ??
                item.item_id ??
                0
            );

        const itemName =
            escapeHTML(
                item.name ||
                item.item_name ||
                "Item"
            );

        const description =
            escapeHTML(
                item.description || ""
            );

        const icon =
            escapeHTML(
                item.icon || "🎁"
            );

        const cost =
            Number(item.cost ?? 0);

        card.innerHTML = `
            <div class="shop-icon">
                ${icon}
            </div>

            <h3>
                ${itemName}
            </h3>

            <p>
                ${description}
            </p>

            <div class="shop-price">
                🪙 ${cost}
            </div>

            <button
                onclick="buyItem(${itemId})"
            >
                Buy
            </button>
        `;

        container.appendChild(card);
    });
}

// ============================================================
// BUY ITEM
// ============================================================

async function buyItem(itemId) {

    console.log(
        "Buying item:",
        itemId
    );

    try {

        const result =
            await apiFetch(
                "/api/shop/buy",
                {
                    method: "POST",

                    body: JSON.stringify({
                        item_id: itemId
                    })
                }
            );

        console.log(
            "Purchase:",
            result
        );

        await refreshDashboard();

        showRewardPopup(
            "ITEM PURCHASED 🛒",
            "Item added to your inventory."
        );

    } catch (error) {

        console.error(
            "Purchase error:",
            error
        );

        alert(
            "Could not buy item:\n\n" +
            error.message
        );
    }
}

// ============================================================
// INVENTORY
// ============================================================

async function loadInventory() {

    try {

        const data =
            await apiFetch("/api/inventory");

        console.log(
            "INVENTORY:",
            data
        );

        const items =
            Array.isArray(data)
                ? data
                : (
                    data.inventory ||
                    data.items ||
                    []
                );

        renderInventory(items);

    } catch (error) {

        console.error(
            "Inventory error:",
            error
        );
    }
}

// ============================================================
// RENDER INVENTORY
// ============================================================

function renderInventory(items) {

    const container =
        document.getElementById(
            "inventoryList"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!items || items.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🎒</div>

                <h3>Inventory Empty</h3>

                <p>
                    Complete quests and visit
                    the shop to collect items.
                </p>
            </div>
        `;

        return;
    }

    items.forEach(function (item) {

        const card =
            document.createElement("div");

        card.className =
            "inventory-item";

        const itemName =
            escapeHTML(
                item.item_name ||
                item.name ||
                "Item"
            );

        const quantity =
            Number(
                item.quantity ?? 1
            );

        card.innerHTML = `
            <div class="inventory-icon">
                🎁
            </div>

            <h3>
                ${itemName}
            </h3>

            <p>
                Quantity: ${quantity}
            </p>
        `;

        container.appendChild(card);
    });
}

// ============================================================
// LOGOUT
// ============================================================

async function logout() {

    try {

        await apiFetch(
            "/api/logout",
            {
                method: "POST"
            }
        );

    } catch (error) {

        console.error(
            "Logout error:",
            error
        );
    }

    window.location.href =
        "/login.html";
}

// ============================================================
// REWARD POPUP
// ============================================================

function showRewardPopup(
    title,
    message
) {

    let popup =
        document.getElementById(
            "rewardPopup"
        );

    if (!popup) {

        popup =
            document.createElement("div");

        popup.id =
            "rewardPopup";

        popup.style.position =
            "fixed";

        popup.style.top =
            "30px";

        popup.style.right =
            "30px";

        popup.style.zIndex =
            "99999";

        popup.style.padding =
            "20px 25px";

        popup.style.borderRadius =
            "16px";

        popup.style.background =
            "#101722";

        popup.style.color =
            "white";

        popup.style.border =
            "1px solid rgba(255,255,255,0.15)";

        popup.style.boxShadow =
            "0 15px 50px rgba(0,0,0,0.5)";

        document.body.appendChild(
            popup
        );
    }

    popup.innerHTML = `
        <strong>
            ${escapeHTML(title)}
        </strong>

        <div style="margin-top:8px;">
            ${escapeHTML(message)}
        </div>
    `;

    popup.style.display =
        "block";

    clearTimeout(
        window.rewardPopupTimer
    );

    window.rewardPopupTimer =
        setTimeout(function () {

            popup.style.display =
                "none";

        }, 3000);
}

// ============================================================
// SET TEXT
// ============================================================

function setText(id, value) {

    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }

    element.textContent =
        value;
}

// ============================================================
// SHOW MESSAGE
// ============================================================

function showMessage(
    element,
    message,
    type
) {

    if (!element) {
        return;
    }

    element.textContent =
        message;

    element.className =
        "message " +
        (type || "info");

    element.style.display =
        "block";
}

// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHTML(value) {

    if (
        value === undefined ||
        value === null
    ) {

        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ============================================================
// CLOSE MODAL WHEN CLICKING OUTSIDE
// ============================================================

document.addEventListener(
    "click",
    function (event) {

        const modal =
            document.getElementById(
                "taskModal"
            );

        if (!modal) {
            return;
        }

        if (event.target === modal) {

            closeTaskModal();
        }
    }
);

// ============================================================
// ESCAPE KEY CLOSES MODAL
// ============================================================

document.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Escape") {

            closeTaskModal();
        }
    }
);

// ============================================================
// GLOBAL FUNCTIONS
// ============================================================

window.openTaskModal =
    openTaskModal;

window.closeTaskModal =
    closeTaskModal;

window.createTask =
    createTask;

window.completeTask =
    completeTask;

window.buyItem =
    buyItem;

window.logout =
    logout;

window.refreshDashboard =
    refreshDashboard;

window.loadDashboard =
    loadDashboard;

window.loadTasks =
    loadTasks;

console.log(
    "RPG TRACKER SCRIPT READY."
);