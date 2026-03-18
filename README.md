# Visiva.AI 营销站自动化测试框架

一个基于 Python + Selenium 的 Web 自动化测试框架，专门用于 [Visiva.AI](https://visiva.ai/app) 的功能测试，支持本地执行和 Jenkins 持续集成。

## 📋 项目概述

本项目仿照 VigilKids 营销站自动化测试框架结构，包含 App 主页面、功能模块导航、Hot Templates 等核心功能的自动化测试，并具备完整的测试报告生成、邮件通知功能。支持部署到 Jenkins 持续集成环境，可配置定时自动执行。

## 🏗️ 项目结构

```
vgai_test/
├── baseView/                    # 基础视图层
│   ├── __init__.py
│   └── baseView.py             # 基础视图类
├── businessView/                # 业务视图层
│   ├── __init__.py
│   ├── appView.py              # App 主页面视图
│   └── featureView.py          # 各功能模块视图
├── common/                      # 公共组件
│   ├── __init__.py
│   ├── caps.py                 # WebDriver 配置管理
│   ├── common_fun.py           # 公共方法和报告管理
│   └── elementlibrary.py       # 页面元素库
├── config/                      # 配置文件
│   └── log.conf                # 日志配置
├── data/                        # 测试数据
│   ├── account.json            # 测试账号数据
│   ├── email_config.json       # 邮件配置
│   └── env.json                # 环境配置
├── logs/                        # 日志文件
├── reports/                     # 测试报告
├── run/                         # 运行脚本
│   ├── __init__.py
│   ├── report.py               # 报告生成和邮件发送
│   └── start.py                # 主启动脚本
├── jenkins/                     # Jenkins 持续集成配置
│   ├── Jenkinsfile             # Jenkins Pipeline 脚本
│   └── jenkins-config.md       # Jenkins 部署配置文档
├── testcase/                    # 测试用例
│   ├── __init__.py
│   └── test_apppage.py         # App 页面功能测试用例
├── requirements.txt
└── README.md
```

## ✨ 主要功能

### 🎯 App 主页面测试
- 主页面加载验证
- 功能入口显示检查（Image to Video、Text to Video、Video Extend、AI Effects）
- Hot Templates 区域验证
- Upgrade、Terms 链接显示

### 🧭 导航功能测试
- Image to Video 页面跳转
- Text to Video 页面跳转
- Video Extend 页面跳转
- AI Effects 页面跳转
- Terms 条款页面跳转

### 📊 测试报告生成
- 详细的 HTML 测试报告
- 测试结果统计
- 运行日志记录

### 📧 通知系统
- 邮件通知：测试完成后可发送邮件，包含报告附件
- 企业微信推送：可配置 webhook 实时推送结果

### 🚀 Jenkins 持续集成
- 支持 Jenkins Pipeline 自动化执行
- 可配置定时任务
- 支持无头浏览器执行

## 🚀 快速开始

### 环境要求
- Python 3.7+
- Chrome 浏览器 (版本 141+)
- ChromeDriver (由 webdriver-manager 自动管理)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置设置

**环境地址 (data/env.json)**
```json
{
    "dev": "https://visiva.ai",
    "prod": "https://visiva.ai"
}
```

**邮件设置 (data/email_config.json)** - 可选
```json
{
    "host": "smtp.qq.com",
    "port": 465,
    "user": "your_email@qq.com",
    "password": "your_app_password",
    "to_addrs": ["recipient@example.com"]
}
```

### 运行测试

**方式一：使用启动脚本（推荐）**
```bash
python run/start.py
```

**方式二：直接运行报告/邮件模块**
```bash
python run/report.py
```

**方式三：Jenkins 持续集成**
- 在 Jenkins 中配置 Pipeline 项目
- 使用 `jenkins/Jenkinsfile` 脚本
- 支持定时自动执行

## 📋 测试用例说明

### AppPageTest 测试类 (test_apppage.py)
- `test_1_app_load`: 主页面加载测试
- `test_2_features_display`: 功能入口显示测试
- `test_3_hot_templates_display`: Hot Templates 区域测试
- `test_4_upgrade_terms_display`: Upgrade/Terms 链接测试
- `test_5~8_nav_*`: 各功能页面导航测试
- `test_9_nav_terms`: Terms 页面跳转测试

### LoginTest 测试类 (test_login.py)
- `test_1_log_in_button_visible`: Log In 按钮可见性测试
- `test_2_click_log_in_open_form`: 点击 Log In 打开登录界面测试
- `test_3_full_login`: 完整登录流程测试（使用 data/account.json）

## 🛠️ 技术架构

- **设计模式**: Page Object Model (POM)、分层架构
- **核心技术**: Selenium WebDriver、unittest、webdriver-manager
- **报告**: 自定义 HTML 报告、日志管理

## 📄 许可证

MIT License
