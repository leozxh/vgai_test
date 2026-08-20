from common.common_fun import Common, By


class Login(Common):
    """登录功能元素定位器"""

    # Log In 按钮
    LOGIN_LOCATORS = [
        (By.XPATH, "//button[contains(., 'Log In')]"),
        (By.XPATH, "//*[contains(text(), 'Log In')]"),
        (By.XPATH, "//a[contains(., 'Log In')]"),
    ]

    EMAIL_LOCATORS = [
        (By.CSS_SELECTOR, 'input[type="email"]'),
        (By.CSS_SELECTOR, 'input[name="email"]'),
        (By.CSS_SELECTOR, 'input[placeholder*="email" i]'),
        (By.CSS_SELECTOR, 'input[placeholder*="Email"]'),
    ]

    PWD_LOCATORS = [
        (By.CSS_SELECTOR, 'input[type="password"]'),
        (By.CSS_SELECTOR, 'input[name="password"]'),
    ]

    BTN_LOCATORS = [
        (By.CSS_SELECTOR, 'button[type="submit"]'),
        (By.XPATH, "//button[contains(text(), 'Login')]"),
        (By.XPATH, "//button[contains(., 'Log in')]"),
        (By.XPATH, "//button[contains(., 'Sign in')]"),
        (By.CSS_SELECTOR, 'input[type="submit"]'),
    ]

    # 登录成功后的显著标识（避免使用 body/nav 这种恒存在元素）
    LOGIN_SUCCESS_LOCATORS = [
        (By.XPATH, "//*[contains(., 'My Creations')]"),
        (By.XPATH, "//*[contains(., 'Upgrade Now')]"),
        (By.XPATH, "//*[contains(., 'AI Effects')]"),
        (By.XPATH, "//button[contains(., 'Log Out') or contains(., 'Logout')]"),
    ]


class AppPage(Common):
    """App 主页面元素定位器"""

    # 页面主标题（SPA 无 h1，优先 document.title；此处作兜底 DOM 检测）
    MAIN_HEADING_LOCATORS = [
        (By.XPATH, "//h1[contains(., 'Visiva')]"),
        (By.XPATH, "//h2[contains(., 'Visiva')]"),
        (By.CSS_SELECTOR, 'h1'),
        (By.XPATH, "//*[contains(@class,'logo') or contains(@class,'brand')][contains(.,'Visiva')]"),
        (By.CSS_SELECTOR, 'img[alt*="isiva"]'),
    ]

    # 新版首页主导航。优先使用路由定位，避免文案或语言变化导致误报。
    PRIMARY_NAV_LOCATORS = {
        'home': [
            (By.CSS_SELECTOR, 'a[href="/app"], a[href$="/app"], a[href$="/app/"]'),
            (By.XPATH, "//a[normalize-space(.)='Home']"),
        ],
        'ai_effects': [
            (By.CSS_SELECTOR, 'a[href*="/app/video-effects"]'),
            (By.XPATH, "//a[contains(normalize-space(.), 'AI Effects')]"),
        ],
        'create': [
            (By.CSS_SELECTOR, 'a[href*="/app/image-to-video"]'),
            (By.XPATH, "//a[normalize-space(.)='Create' or contains(normalize-space(.), 'Image to Video')]"),
        ],
        'apps': [
            (By.CSS_SELECTOR, 'a[href*="/app/ai-tools"]'),
            (By.XPATH, "//a[normalize-space(.)='Apps']"),
        ],
        'creations': [
            (By.CSS_SELECTOR, 'a[href*="/app/creations"]'),
            (By.XPATH, "//a[normalize-space(.)='Creations' or contains(normalize-space(.), 'My Creations')]"),
        ],
    }

    # 新版首页内容区：原 Hot Templates 已调整为 Hot + Models。
    HOT_SECTION_LOCATORS = [
        (By.XPATH, "//*[self::h1 or self::h2 or self::h3][contains(normalize-space(.), 'Hot')]"),
        (By.XPATH, "//*[contains(normalize-space(.), '🔥 Hot')]"),
    ]

    MODELS_SECTION_LOCATORS = [
        (By.XPATH, "//*[self::h1 or self::h2 or self::h3][normalize-space(.)='Models']"),
        (By.XPATH, "//button[contains(normalize-space(.), 'View All Models')]"),
    ]

    # 新版页脚公司政策入口（旧版 Upgrade/Terms 展示项已移除）。
    COMPANY_POLICY_LOCATORS = {
        'privacy': [
            (By.CSS_SELECTOR, 'a[href*="privacy-policy"]'),
        ],
        'refund': [
            (By.CSS_SELECTOR, 'a[href*="refund-policy"]'),
        ],
        'dmca': [
            (By.CSS_SELECTOR, 'a[href*="dmca"]'),
        ],
    }

    # 兼容仍使用该名称的其他测试逻辑。
    HOT_TEMPLATES_LOCATORS = [
        *HOT_SECTION_LOCATORS,
        *MODELS_SECTION_LOCATORS,
    ]

    # Upgrade
    UPGRADE_LOCATORS = [
        (By.XPATH, "//*[contains(translate(text(), 'UPGRADE', 'upgrade'), 'upgrade')]"),
        (By.XPATH, "//button[contains(., 'Upgrade')]"),
    ]

    # Terms
    TERMS_LOCATORS = [
        (By.XPATH, "//*[contains(text(), 'Terms')]"),
        (By.CSS_SELECTOR, 'a[href*="terms"]'),
    ]

    # 功能入口
    IMAGE_TO_VIDEO_LOCATORS = [
        (By.XPATH, "//*[contains(., 'Image to Video')][not(.//*[contains(., 'Image to Video')])]"),
        (By.CSS_SELECTOR, 'a[href*="image-to-video"]'),
    ]

    TEXT_TO_VIDEO_LOCATORS = [
        (By.XPATH, "//*[contains(., 'Text to Video')][not(.//*[contains(., 'Text to Video')])]"),
        (By.CSS_SELECTOR, 'a[href*="text-to-video"]'),
    ]

    VIDEO_EXTEND_LOCATORS = [
        (By.XPATH, "//*[contains(., 'Video Extend')][not(.//*[contains(., 'Video Extend')])]"),
        (By.CSS_SELECTOR, 'a[href*="video-extend"]'),
    ]

    AI_EFFECTS_LOCATORS = [
        (By.XPATH, "//*[contains(., 'AI Effects')][not(.//*[contains(., 'AI Effects')])]"),
        (By.CSS_SELECTOR, 'a[href*="video-effects"]'),
    ]


class ImageToVideo(Common):
    """Image to Video 页面元素定位器"""

    # Inspiration 按钮
    INSPIRATION_BTN_LOCATORS = [
        (By.XPATH, "//button[contains(text(), 'Inspiration')]"),
        (By.XPATH, "//*[contains(text(), 'Inspiration')]"),
    ]

    # Inspiration 面板中的模板图片（第一个可点击的模板）
    INSPIRATION_TEMPLATE_LOCATORS = [
        (By.CSS_SELECTOR, 'img[src*="Try_a_sample"]'),
        (By.XPATH, "//img[contains(@src, 'Try_a_sample')]"),
    ]

    # Prompt 输入框
    PROMPT_TEXTAREA_LOCATORS = [
        (By.CSS_SELECTOR, 'textarea'),
        (By.XPATH, "//textarea[contains(@placeholder, 'Describe')]"),
    ]

    # Create / Generate 按钮
    CREATE_BTN_LOCATORS = [
        (By.XPATH, "//button[contains(., 'Create')]"),
        (By.XPATH, "//button[contains(text(), 'Create')]"),
        (By.XPATH, "//button[contains(., 'Generate')]"),
        (By.XPATH, "//button[contains(text(), 'Generate')]"),
    ]

    # 生成错误提示（用于反向校验：不应出现）
    ERROR_TOAST_LOCATORS = [
        (By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'Error')]"),
        (By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'Error') or contains(text(), 'failed')]"),
    ]

    # 生成中/生成成功的标识
    GENERATION_PROGRESS_LOCATORS = [
        (By.XPATH, "//*[contains(text(), 'Generating') or contains(text(), 'generating')]"),
        (By.XPATH, "//*[contains(text(), 'Queuing') or contains(text(), 'queuing') or contains(text(), 'Queue')]"),
        (By.XPATH, "//*[contains(text(), 'Processing') or contains(text(), 'processing')]"),
    ]
