// ============================================================
// RPG TRACKER - FRONTEND JAVASCRIPT
// ============================================================

const API_URL = "http://127.0.0.1:5000";


// ============================================================
// HELPER FUNCTIONS
// ============================================================

function setText(id, value) {

    const element = document.getElementById(id);

    if (element) {
        element.textContent = value ?? "";
    }
}


function getElement(id) {
    return document.getElementById(id);
}


// ============================================================
// REGISTER
// ============================================================

const registerForm = getElement("registerForm");

if (registerForm) {

    registerForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const username =
            getElement("username").value.trim();

        const email =
            getElement("email").value.trim();

        const password =
            getElement("password").value;

        const message =
            getElement("registerMessage");

        try {

            const response = await fetch(
                `${API_URL}/api/register`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    credentials: "include",

                    body: JSON.stringify({
                        username,
                        email,
                        password
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {

                message.textContent =
                    data.message || "Registration failed.";

                message.style.color = "#ff7b7b";

                return;
            }

            message.textContent =
                "Character created! Redirecting...";

            message.style.color = "#72e4ca";

            setTimeout(() => {

                window.location.href = "login.html";

            }, 1000);

        } catch (error) {

            console.error("Registration error:", error);

            message.textContent =
                "Cannot connect to RPG Tracker server.";

            message.style.color = "#ff7b7b";
        }
    });
}


// ============================================================
// LOGIN
// ============================================================

const loginForm = getElement("loginForm");

if (loginForm) {

    loginForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const login =
            getElement("loginUsername").value.trim();

        const password =
            getElement("loginPassword").value;

        const message =
            getElement("loginMessage");

        const button =
            getElement("loginButton");

        button.disabled = true;

        button.textContent = "Entering...";

        try {

            const response = await fetch(
                `${API_URL}/api/login`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    credentials: "include",

                    body: JSON.stringify({
                        login,
                        password
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {

                message.textContent =
                    data.message || "Login failed.";

                message.style.color = "#ff7b7b";

                button.disabled = false;

                button.textContent = "Enter World";

                return;
            }

            message.textContent =
                "Login successful! Entering world...";

            message.style.color = "#72e4ca";

            setTimeout(() => {

                window.location.href = "dashboard.html";

            }, 600);

        } catch (error) {

            console.error("Login error:", error);

            message.textContent =
                "Cannot connect to server.";

            message.style.color = "#ff7b7b";

            button.disabled = false;

            button.textContent = "Enter World";
        }
    });
}


// ============================================================
// DASHBOARD START
// ============================================================

if (
    getElement("questList") ||
    getElement("shopList") ||
    getElement("inventoryList")
) {

    initializeDashboard();
}


// ============================================================
// INITIALIZE DASHBOARD
// ============================================================

async function initializeDashboard() {

    await loadDashboard();

    await loadTasks();

    await loadShop();

    await loadInventory();
}


// ============================================================
// LOAD DASHBOARD
// ============================================================

async function loadDashboard() {

    try {

        const response = await fetch(
            `${API_URL}/api/dashboard`,
            {
                method: "GET",
                credentials: "include"
            }
        );

        if (response.status === 401) {

            window.location.href = "login.html";

            return false;
        }

        const data = await response.json();

        if (!response.ok || !data.success) {

            console.error(
                "Dashboard error:",
                data
            );

            return false;
        }

        updatePlayerUI(
            data.user,
            data.attributes
        );

        return true;

    } catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );

        return false;
    }
}


// ============================================================
// UPDATE PLAYER UI
// ============================================================

function updatePlayerUI(user, attributes) {

    if (!user) return;

    setText(
        "username",
        user.username
    );

    setText(
        "characterName",
        user.username
    );

    setText(
        "level",
        user.level
    );

    setText(
        "xp",
        user.xp
    );

    setText(
        "navCoins",
        user.coins
    );

    setText(
        "statXP",
        user.xp
    );

    setText(
        "statCoins",
        user.coins
    );

    setText(
        "statStreak",
        user.current_streak ?? 0
    );

    setText(
        "shopCoins",
        user.coins
    );


    // ========================================================
    // XP PROGRESS
    // ========================================================

    const nextLevelXP =
        user.level * 100;

    setText(
        "xpNext",
        nextLevelXP
    );

    const xpPercentage =
        Math.min(
            (user.xp / nextLevelXP) * 100,
            100
        );

    const xpProgress =
        getElement("xpProgress");

    if (xpProgress) {

        xpProgress.style.width =
            `${xpPercentage}%`;
    }


    // ========================================================
    // ATTRIBUTES
    // ========================================================

    if (attributes) {

        updateAttribute(
            "strength",
            attributes.strength ?? 1
        );

        updateAttribute(
            "intelligence",
            attributes.intelligence ?? 1
        );

        updateAttribute(
            "discipline",
            attributes.discipline ?? 1
        );

        updateAttribute(
            "creativity",
            attributes.creativity ?? 1
        );

        updateAttribute(
            "social",
            attributes.social ?? 1
        );
    }
}


// ============================================================
// ATTRIBUTE UI
// ============================================================

function updateAttribute(name, value) {

    setText(
        name,
        value
    );

    const bar =
        getElement(`${name}Bar`);

    if (bar) {

        const percentage =
            Math.min(
                Number(value) * 10,
                100
            );

        bar.style.width =
            `${percentage}%`;
    }
}


// ============================================================
// LOAD QUESTS
// ============================================================

async function loadTasks() {

    const list =
        getElement("questList");

    if (!list) return;

    try {

        const response = await fetch(
            `${API_URL}/api/tasks`,
            {
                credentials: "include"
            }
        );

        if (response.status === 401) {

            window.location.href = "login.html";

            return;
        }

        const data =
            await response.json();

        if (!response.ok || !data.success) {

            console.error(
                "Task loading error:",
                data
            );

            return;
        }

        renderTasks(
            data.tasks || []
        );

    } catch (error) {

        console.error(
            "Task error:",
            error
        );
    }
}


// ============================================================
// RENDER QUESTS
// ============================================================

function renderTasks(tasks) {

    const list =
        getElement("questList");

    const empty =
        getElement("emptyQuests");

    const statQuests =
        getElement("statQuests");

    if (!list) return;

    list.innerHTML = "";


    // ========================================================
    // QUEST COUNT
    // ========================================================

    const completedCount =
        tasks.filter(
            task => task.completed
        ).length;

    if (statQuests) {

        statQuests.textContent =
            completedCount;
    }


    // ========================================================
    // EMPTY STATE
    // ========================================================

    if (!tasks.length) {

        if (empty) {

            empty.style.display =
                "block";
        }

        return;
    }


    if (empty) {

        empty.style.display =
            "none";
    }


    // ========================================================
    // CREATE QUEST CARDS
    // ========================================================

    tasks.forEach(task => {

        const item =
            document.createElement("div");

        item.className =
            "quest-item";


        if (task.completed) {

            item.classList.add(
                "completed-quest"
            );
        }


        item.innerHTML = `

            <div class="quest-item-header">

                <div>

                    <h3>
                        ${escapeHTML(task.title)}
                    </h3>

                    <span class="quest-category">
                        ${escapeHTML(task.category || "Personal")}
                    </span>

                </div>

                ${
                    task.completed
                    ? "<span>✅</span>"
                    : ""
                }

            </div>


            <p class="quest-description">
                ${escapeHTML(task.description || "")}
            </p>


            <div class="quest-reward-display">

                <span>
                    ⚡ +${Number(task.xp_reward || 0)} XP
                </span>

                <span>
                    🪙 +${Number(task.coin_reward || 0)} Coins
                </span>

            </div>


            ${
                task.completed

                ? `

                    <button
                        class="complete-quest-btn"
                        disabled
                    >
                        ✓ Completed
                    </button>

                `

                : `

                    <button
                        class="complete-quest-btn"
                        onclick="completeQuest(${Number(task.id)})"
                    >
                        Complete Quest
                    </button>

                `
            }

        `;


        list.appendChild(item);

    });
}


// ============================================================
// QUEST MODAL
// ============================================================

const createQuestButton =
    getElement("createQuestButton");

const createFirstQuest =
    getElement("createFirstQuest");

const questModal =
    getElement("questModal");

const closeQuestModal =
    getElement("closeQuestModal");


function openQuestModal() {

    if (questModal) {

        questModal.classList.add("active");
    }
}


function closeQuestModalFunction() {

    if (questModal) {

        questModal.classList.remove("active");
    }
}


if (createQuestButton) {

    createQuestButton.addEventListener(
        "click",
        openQuestModal
    );
}


if (createFirstQuest) {

    createFirstQuest.addEventListener(
        "click",
        openQuestModal
    );
}


if (closeQuestModal) {

    closeQuestModal.addEventListener(
        "click",
        closeQuestModalFunction
    );
}


if (questModal) {

    questModal.addEventListener(
        "click",
        function (event) {

            if (event.target === questModal) {

                closeQuestModalFunction();
            }
        }
    );
}


// ============================================================
// CREATE QUEST
// ============================================================

const questForm =
    getElement("questForm");

if (questForm) {

    questForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const title =
                getElement("questTitle").value.trim();

            const description =
                getElement("questDescription").value.trim();

            const category =
                getElement("questCategory").value;

            const message =
                getElement("questMessage");

            const button =
                getElement("questSubmitButton");


            if (!title) {

                message.textContent =
                    "Quest title is required.";

                message.style.color =
                    "#ff7b7b";

                return;
            }


            button.disabled = true;

            button.textContent =
                "Creating...";


            try {

                const response =
                    await fetch(
                        `${API_URL}/api/tasks`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            credentials:
                                "include",

                            body:
                                JSON.stringify({
                                    title,
                                    description,
                                    category
                                })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    message.textContent =
                        data.message ||
                        "Could not create quest.";

                    message.style.color =
                        "#ff7b7b";

                    return;
                }


                message.textContent =
                    "Quest created successfully!";

                message.style.color =
                    "#72e4ca";


                questForm.reset();


                await loadTasks();


                setTimeout(
                    closeQuestModalFunction,
                    500
                );


            } catch (error) {

                console.error(
                    "Create quest error:",
                    error
                );

                message.textContent =
                    "Server connection failed.";

                message.style.color =
                    "#ff7b7b";

            } finally {

                button.disabled = false;

                button.textContent =
                    "Create Quest";
            }
        }
    );
}


// ============================================================
// COMPLETE QUEST
// ============================================================

async function completeQuest(taskId) {

    try {

        const response =
            await fetch(
                `${API_URL}/api/tasks/${taskId}/complete`,
                {
                    method: "PUT",
                    credentials: "include"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            showShopNotification(
                data.error ||
                data.message ||
                "Could not complete quest.",
                true
            );

            return;
        }


        // ====================================================
        // SHOW REWARD
        // ====================================================

        showRewardAnimation(
            data.reward,
            data.player?.level_ups || 0,
            data.player?.current_streak || 0
        );


        // ====================================================
        // REFRESH PLAYER
        // ====================================================

        await loadDashboard();

        await loadTasks();

    } catch (error) {

        console.error(
            "Complete quest error:",
            error
        );

        showShopNotification(
            "Server connection failed.",
            true
        );
    }
}


// ============================================================
// REWARD ANIMATION
// ============================================================

function showRewardAnimation(
    reward,
    levelUps,
    streak
) {

    const oldPopup =
        document.querySelector(
            ".reward-popup"
        );

    if (oldPopup) {

        oldPopup.remove();
    }


    const popup =
        document.createElement("div");

    popup.className =
        "reward-popup";


    popup.innerHTML = `

        <div class="reward-icon">
            🎉
        </div>

        <strong>
            Quest Complete!
        </strong>

        <span>
            ⚡ +${Number(reward?.xp || 0)} XP
        </span>

        <span>
            🪙 +${Number(reward?.coins || 0)} Coins
        </span>

        <span>
            🔥 ${Number(streak || 0)} Day Streak
        </span>

        ${
            levelUps > 0

            ? `

                <div class="level-up-text">
                    ⬆️ LEVEL UP!
                </div>

            `

            : ""
        }

    `;


    document.body.appendChild(
        popup
    );


    requestAnimationFrame(() => {

        popup.classList.add(
            "show"
        );

    });


    setTimeout(() => {

        popup.classList.remove(
            "show"
        );

        setTimeout(
            () => popup.remove(),
            500
        );

    }, 3500);
}


// ============================================================
// LOAD SHOP
// ============================================================

async function loadShop() {

    const shopList =
        getElement("shopList");

    if (!shopList) return;


    try {

        const response =
            await fetch(
                `${API_URL}/api/shop`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            window.location.href =
                "login.html";

            return;
        }


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            shopList.innerHTML = `

                <div class="shop-loading">
                    Could not load shop.
                </div>

            `;

            return;
        }


        renderShop(
            data.items || []
        );


    } catch (error) {

        console.error(
            "Shop loading error:",
            error
        );


        shopList.innerHTML = `

            <div class="shop-loading">
                Shop connection failed.
            </div>

        `;
    }
}


// ============================================================
// RENDER SHOP
// ============================================================

function renderShop(items) {

    const shopList =
        getElement("shopList");

    if (!shopList) return;


    if (!items.length) {

        shopList.innerHTML = `

            <div class="shop-loading">
                No rewards available.
            </div>

        `;

        return;
    }


    shopList.innerHTML =
        items.map(item => `

            <div class="shop-item">

                <div class="shop-item-icon">
                    ${item.icon || "🎁"}
                </div>

                <span class="shop-item-type">
                    ${escapeHTML(item.type || "Reward")}
                </span>

                <h3>
                    ${escapeHTML(item.name || "Unknown Item")}
                </h3>

                <p class="shop-item-description">
                    ${escapeHTML(item.description || "")}
                </p>

                <div class="shop-item-footer">

                    <span class="shop-price">
                        🪙 ${Number(item.cost || 0)}
                    </span>

                    <button
                        class="buy-item-btn"
                        onclick="buyItem(${Number(item.id)})"
                        type="button"
                    >
                        BUY
                    </button>

                </div>

            </div>

        `).join("");
}


// ============================================================
// BUY SHOP ITEM
// ============================================================

async function buyItem(itemId) {

    const buttons =
        document.querySelectorAll(
            ".buy-item-btn"
        );


    // Prevent accidental double-click

    buttons.forEach(button => {

        button.disabled = true;

    });


    try {

        const response =
            await fetch(
                `${API_URL}/api/shop/buy`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    credentials:
                        "include",

                    body:
                        JSON.stringify({
                            item_id: Number(itemId)
                        })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            showShopNotification(
                data.error ||
                data.message ||
                "Purchase failed.",
                true
            );

            return;
        }


        // ====================================================
        // SUCCESS
        // ====================================================

        showShopNotification(
            `🎉 ${data.message || "Item purchased!"}`
        );


        // Update coins

        if (typeof data.coins !== "undefined") {

            setText(
                "navCoins",
                data.coins
            );

            setText(
                "statCoins",
                data.coins
            );

            setText(
                "shopCoins",
                data.coins
            );
        }


        // Refresh inventory

        await loadInventory();


    } catch (error) {

        console.error(
            "Purchase error:",
            error
        );

        showShopNotification(
            "Server connection failed.",
            true
        );

    } finally {

        buttons.forEach(button => {

            button.disabled = false;

        });
    }
}


// ============================================================
// LOAD INVENTORY
// ============================================================

async function loadInventory() {

    const inventoryList =
        getElement("inventoryList");

    if (!inventoryList) return;


    try {

        const response =
            await fetch(
                `${API_URL}/api/inventory`,
                {
                    credentials: "include"
                }
            );


        if (response.status === 401) {

            window.location.href =
                "login.html";

            return;
        }


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            inventoryList.innerHTML = `

                <div class="shop-loading">
                    Could not load inventory.
                </div>

            `;

            return;
        }


        renderInventory(
            data.items || []
        );


    } catch (error) {

        console.error(
            "Inventory loading error:",
            error
        );


        inventoryList.innerHTML = `

            <div class="shop-loading">
                Inventory connection failed.
            </div>

        `;
    }
}


// ============================================================
// RENDER INVENTORY
// ============================================================

function renderInventory(items) {

    const inventoryList =
        getElement("inventoryList");

    if (!inventoryList) return;


    if (!items.length) {

        inventoryList.innerHTML = `

            <div class="empty-inventory">

                <div style="font-size: 42px;">
                    🎒
                </div>

                <p>
                    Your inventory is empty.
                </p>

                <small>
                    Complete quests and visit the shop
                    to collect rewards.
                </small>

            </div>

        `;

        return;
    }


    inventoryList.innerHTML =
        items.map(item => `

            <div class="inventory-item">

                <div class="inventory-icon">
                    ${getItemIcon(item.item_name)}
                </div>

                <div class="inventory-info">

                    <h3>
                        ${escapeHTML(item.item_name)}
                    </h3>

                    <p>
                        ${escapeHTML(item.item_type || "Item")}
                    </p>

                </div>

                <span class="inventory-quantity">
                    ×${Number(item.quantity || 1)}
                </span>

            </div>

        `).join("");
}


// ============================================================
// ITEM ICON
// ============================================================

function getItemIcon(itemName) {

    const icons = {

        "Iron Sword": "⚔️",

        "Guardian Shield": "🛡️",

        "Health Potion": "🧪",

        "Magic Book": "📕",

        "Golden Crown": "👑"

    };

    return icons[itemName] || "🎁";
}


// ============================================================
// SHOP NOTIFICATION
// ============================================================

function showShopNotification(
    message,
    error = false
) {

    const old =
        document.querySelector(
            ".shop-notification"
        );

    if (old) {

        old.remove();
    }


    const notification =
        document.createElement(
            "div"
        );


    notification.className =
        "shop-notification";


    if (error) {

        notification.classList.add(
            "error"
        );
    }


    notification.textContent =
        message;


    document.body.appendChild(
        notification
    );


    requestAnimationFrame(() => {

        notification.classList.add(
            "show"
        );

    });


    setTimeout(() => {

        notification.classList.remove(
            "show"
        );

        setTimeout(
            () => notification.remove(),
            400
        );

    }, 3000);
}


// ============================================================
// LOGOUT
// ============================================================

const logoutButton =
    getElement("logoutButton");


if (logoutButton) {

    logoutButton.addEventListener(
        "click",
        async function () {

            logoutButton.disabled = true;

            logoutButton.textContent =
                "Logging out...";


            try {

                await fetch(
                    `${API_URL}/api/logout`,
                    {
                        method: "POST",
                        credentials: "include"
                    }
                );

            } catch (error) {

                console.error(
                    "Logout error:",
                    error
                );

            } finally {

                window.location.href =
                    "login.html";
            }
        }
    );
}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHTML(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value ?? "";

    return div.innerHTML;
}