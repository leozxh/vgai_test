from common.common_fun import Common, By


class Login(Common):
    """登录功能元素定位器"""

    # Log In 按钮
    LOGIN_LOCATORS = [
        (By.XPATH, "//button[contains(., 'Log In')]"),
        (By.XPATH, "//*[contains(text(), 'Log In')]"),
        (By.CSS_SELECTOR, 'button:contains("Log In")'),
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

    LOGIN_SUCCESS_LOCATORS = [
        (By.XPATH, "//body"),
        (By.CSS_SELECTOR, 'nav'),
        (By.CSS_SELECTOR, 'header nav'),
    ]


class AppPage(Common):
    """App 主页面元素定位器"""

    # 页面主标题
    MAIN_HEADING_LOCATORS = [
        (By.XPATH, "//h1[contains(., 'Visiva')]"),
        (By.CSS_SELECTOR, 'h1'),
    ]

    # Hot Templates
    HOT_TEMPLATES_LOCATORS = [
        (By.XPATH, "//h2[contains(., 'Hot Templates')]"),
        (By.XPATH, "//*[contains(text(), 'Hot Templates')]"),
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
