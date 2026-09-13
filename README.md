# 🎮 RPG Tracker

> Turn your real life into an RPG. Complete quests, earn XP, build streaks, collect coins, buy rewards, and level up.

## 🌟 Overview

RPG Tracker is a gamified productivity web application that transforms everyday tasks and personal goals into RPG-style quests.

Users can create tasks, complete quests, earn XP and coins, build streaks, improve character attributes, purchase rewards, and maintain their progress using a PostgreSQL database.

## 🎯 Problem Statement

Traditional task-management applications often focus only on checklists. Users may lose motivation because there is little sense of progression, achievement, or reward.

RPG Tracker solves this problem by turning everyday goals into game-style quests.

## 💡 Solution

```text
Real-Life Task
      ↓
Complete Quest
      ↓
Earn XP + Coins
      ↓
Build Streak
      ↓
Improve Attributes
      ↓
Level Up
      ↓
Buy Rewards
      ↓
Continue the Journey
```

## ✨ Key Features

* 🔐 User registration and login
* ⚔️ Create and manage quests
* ⭐ Earn XP from completed quests
* 🆙 Nonlinear level progression
* 🔥 Daily streak tracking
* 🧙 Character attributes
* 🪙 Coin reward system
* 🛒 In-app reward shop
* 🎒 Inventory system
* 💾 PostgreSQL database persistence
* ☁️ Cloud deployment
* ✨ RPG-themed animated interface
* 📱 Responsive design

## 🧙 Character Attributes

RPG Tracker includes five character attributes:

* 💪 Strength
* 🧠 Intelligence
* 🎯 Discipline
* 🎨 Creativity
* 🤝 Social

Task categories can contribute to different character attributes.

## ⭐ XP & Level System

Completing quests gives the player XP.

The application uses nonlinear XP progression, meaning higher levels require progressively more XP.

```text
Level 1 → Level 2 → Level 3 → Level 4 → ...
             Increasing XP requirements
```

## 🔥 Streak System

The application tracks user consistency through:

* Current streak
* Longest streak

This encourages users to continue completing quests regularly.

## 🪙 Reward Economy

Users earn coins when completing quests.

Coins can be used to purchase rewards from the shop.

Example rewards:

* Health Potion
* Iron Sword
* Magic Book
* Golden Shield
* Legendary Crown

Purchased items are stored in the user's inventory.

## 🗄️ Database

RPG Tracker uses PostgreSQL for persistent storage.

Main tables:

```text
users
tasks
attributes
inventory
```

User progress is stored in the database rather than relying only on browser localStorage.

## 🏗️ Technology Stack

| Component         | Technology                        |
| ----------------- | --------------------------------- |
| Frontend          | HTML5, CSS3, JavaScript           |
| Backend           | Python                            |
| Framework         | Flask                             |
| Database          | PostgreSQL                        |
| Database Driver   | psycopg2                          |
| Authentication    | Flask Sessions + Password Hashing |
| Production Server | Gunicorn                          |
| Version Control   | Git                               |
| Repository        | GitHub                            |
| Deployment        | Render                            |

## 🔄 Application Flow

```text
Landing Page
     ↓
Register / Login
     ↓
Dashboard
     ↓
Create Quest
     ↓
Complete Quest
     ↓
XP + Coins
     ↓
Level / Streak / Attributes
     ↓
Reward Shop
     ↓
Inventory
```

## 🔒 Security

The project uses basic security practices including:

* Password hashing
* Session-based authentication
* Environment variables for secrets
* `.env` excluded from Git
* Virtual environment excluded from Git
* User-specific database operations
* Production server configuration

**Never commit passwords, database credentials, or `.env` files to GitHub.**

## 🚀 Local Installation

### Clone the repository

```bash
git clone https://github.com/titughorai12/RPG_Tracker.git
cd RPG_Tracker
```

### Create a virtual environment

```bash
python -m venv venv
```

### Activate it on Windows PowerShell

```powershell
venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file inside the `backend` folder.

Example:

```env
SECRET_KEY=your-secret-key
POSTGRES_HOST=your-host
POSTGRES_PORT=5432
POSTGRES_DB=your-database
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-password
POSTGRES_SSLMODE=require
```

Do not put real passwords in this README or GitHub.

### Run the application

```bash
cd backend
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## ☁️ Deployment

The application is deployed using Render.

```text
User Browser
     ↓
Render Web Service
     ↓
Flask Backend
     ↓
PostgreSQL Database
```

Gunicorn is used as the production web server.

## 🌐 Live Demo

**Live Application:**
https://rpg-tracker-kcjp.onrender.com

**GitHub Repository:**
https://github.com/titughorai12/RPG_Tracker

## 🎥 Demo Flow

The main demonstration flow is:

```text
Register
 ↓
Login
 ↓
Create Quest
 ↓
Complete Quest
 ↓
XP increases
 ↓
Coins increase
 ↓
Streak updates
 ↓
Open Shop
 ↓
Buy Reward
 ↓
Check Inventory
 ↓
Refresh
 ↓
Data remains saved
```

## 🔮 Future Scope

Future improvements could include:

* 🏆 Achievements and badges
* 👥 Friends and social challenges
* 🏅 Leaderboards
* 📊 Advanced analytics
* 🔔 Notifications
* 🗺️ Quest maps
* 🎨 Character customization
* 🤖 AI-powered task recommendations
* 📱 Mobile application
* 🎁 More rewards and game mechanics

## 🏆 Conclusion

RPG Tracker transforms ordinary productivity into an engaging RPG experience.

Instead of simply asking:

**"What tasks do I need to complete?"**

the application encourages users to think:

**"What quest will I complete today?"**

---

### 👨‍💻 Project

**RPG Tracker**

Built with:

**HTML + CSS + JavaScript + Flask + PostgreSQL**

Created for educational and hackathon purposes.
