"""Credit deduction matrix verification.

Run:
    python testcase/test_credits.py

Outputs:
    D:\\chrome\\download\\credits_report.html
    D:\\chrome\\download\\credits_report.json
"""

import html
import json
import logging
import os
import sys
import time
from datetime import datetime
from itertools import product
from urllib.parse import urlsplit

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.caps import DriverManager
from businessView.siginView import SiginView
from businessView.creditsView import CreditsView


DEFAULT_PROMPT = "A beautiful sunset over the ocean, cinematic lighting"
OUTPUT_DIR = os.environ.get("CREDITS_OUTPUT_DIR", r"D:\chrome\download")
CREDITS_BASE_URL = os.environ.get("CREDITS_BASE_URL", "").strip()
CREDITS_USERNAME = os.environ.get("CREDITS_USERNAME", "").strip()
CREDITS_PASSWORD = os.environ.get("CREDITS_PASSWORD", "").strip()
TEST_IMAGE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "screenshots",
    "discover_Image_to_Video_1775486099.png",
)
TEST_VIDEO = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "test_video.mp4",
)

ONLY_PAGES = {
    p.strip().lower()
    for p in os.environ.get("ONLY_PAGES", "").split(",")
    if p.strip()
}
MAX_CASES = int(os.environ.get("MAX_CASES", "0") or "0")
SKIP_CASES = int(os.environ.get("SKIP_CASES", "0") or "0")
CASE_INDICES = {
    int(item.strip())
    for item in os.environ.get("CASE_INDICES", "").split(",")
    if item.strip()
}
WAIT_DEDUCTION_SECONDS = int(os.environ.get("WAIT_DEDUCTION_SECONDS", "75") or "75")
WAIT_CREATIONS_IDLE = os.environ.get("WAIT_CREATIONS_IDLE", "").lower() in (
    "1",
    "true",
    "yes",
)
CREATIONS_IDLE_TIMEOUT = int(os.environ.get("CREATIONS_IDLE_TIMEOUT", "3600") or "3600")
CREATIONS_IDLE_POLL = int(os.environ.get("CREATIONS_IDLE_POLL", "30") or "30")
MANUAL_LOGIN = os.environ.get("MANUAL_LOGIN", "").lower() in ("1", "true", "yes")
MANUAL_LOGIN_TIMEOUT = int(os.environ.get("MANUAL_LOGIN_TIMEOUT", "600") or "600")


PAGES = [
    {
        "key": "i2v",
        "page": "Image to Video",
        "path": "/app/image-to-video",
        "requires": "image",
        "models": [
            {
                "name": "Visiva Intimate R4.5",
                "duration": ["5s", "8s", "10s", "15s"],
                "resolution": ["720P", "1080P"],
            },
            {
                "name": "Visiva Intimate R4.0",
                "duration": ["5s", "10s"],
                "resolution": ["480P", "720P", "1080P"],
            },
            {
                "name": "Visiva Pro T3.0",
                "duration": ["5s", "8s"],
                "resolution": ["360P", "540P", "720P", "1080P"],
            },
            {
                "name": "Visiva Pro T2.0",
                "duration": ["-"],
                "resolution": ["720P", "1080P"],
            },
        ],
    },
    {
        "key": "t2v",
        "page": "Text to Video",
        "path": "/app/text-to-video",
        "requires": "prompt",
        "models": [
            {
                "name": "Visiva Intimate R4.0",
                "duration": ["5s", "10s"],
                "resolution": ["480P", "720P", "1080P"],
                "ratio": ["9:16", "16:9"],
            },
            {
                "name": "Visiva Pro T3.0",
                "cases": [
                    {
                        "duration": ["5s", "8s"],
                        "resolution": ["360P", "540P", "720P", "1080P"],
                        "ratio": ["9:16", "16:9", "1:1", "3:4", "4:3"],
                    },
                    {
                        "duration": ["10s"],
                        "resolution": ["360P", "540P", "720P"],
                        "ratio": ["9:16", "16:9", "1:1", "3:4", "4:3"],
                    },
                ],
            },
            {
                "name": "Visiva Pro T2.0",
                "cases": [
                    {
                        "duration": ["8s"],
                        "resolution": ["720P", "1080P"],
                        "ratio": ["9:16", "1:1", "3:4", "4:3"],
                    },
                ],
            },
        ],
    },
    {
        "key": "ve",
        "page": "Video Extend",
        "path": "/app/video-extend",
        "requires": "video",
        "models": [
            {
                "name": "-",
                "duration": ["5s", "8s"],
            },
        ],
    },
    {
        "key": "i2i",
        "page": "Image to Image",
        "path": "/app/image-to-image",
        "requires": "image",
        "models": [
            {"name": "Nano Banana Pro", "quality": ["1K", "2K", "4K"]},
            {"name": "Nano Banana", "quality": ["1K", "2K"]},
            {"name": "Visiva Intimate R4.0", "quality": ["1K", "2K", "4K"]},
        ],
    },
    {
        "key": "t2i",
        "page": "Text to Image",
        "path": "/app/text-to-image",
        "requires": "prompt",
        "models": [
            {
                "name": "Nano Banana Pro",
                "quality": ["1K", "2K", "4K"],
                "ratio": ["1:1", "9:16", "16:9", "3:4", "4:3", "2:3", "3:2"],
            },
            {
                "name": "Nano Banana",
                "quality": ["1K", "2K"],
                "ratio": ["1:1", "9:16", "16:9", "3:4", "4:3", "2:3", "3:2"],
            },
            {
                "name": "Visiva Intimate R4.0",
                "quality": ["1K", "2K", "4K"],
                "ratio": ["1:1", "9:16", "16:9", "3:4", "4:3"],
            },
        ],
    },
]

ALL_MODELS = sorted(
    {m["name"] for p in PAGES for m in p["models"] if m["name"] != "-"},
    key=len,
    reverse=True,
)


def norm_text(value):
    return " ".join((value or "").split())


def origin(driver):
    parsed = urlsplit(driver.current_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return "https://visiva.top"


def expand_model_cases(model):
    case_groups = model.get("cases") or [model]
    for group in case_groups:
        durations = group.get("duration") or ["-"]
        resolutions = group.get("resolution") or ["-"]
        qualities = group.get("quality") or ["-"]
        ratios = group.get("ratio") or ["-"]
        for duration, resolution, quality, ratio in product(
            durations, resolutions, qualities, ratios
        ):
            yield {
                "duration": duration,
                "resolution": resolution,
                "quality": quality,
                "ratio": ratio,
            }


def case_iter():
    count = 0
    for page in PAGES:
        if ONLY_PAGES and page["key"].lower() not in ONLY_PAGES:
            continue
        for model in page["models"]:
            for params in expand_model_cases(model):
                count += 1
                if CASE_INDICES and count not in CASE_INDICES:
                    continue
                if SKIP_CASES and count <= SKIP_CASES:
                    continue
                if MAX_CASES and count > MAX_CASES:
                    return
                yield count, page, model, params


class CreditMatrixRunner:
    def __init__(self):
        self.driver_manager = DriverManager()
        if CREDITS_BASE_URL:
            self.driver_manager.config["test"] = CREDITS_BASE_URL
        self.driver = None
        self.cv = None
        self.results = []

    def run(self):
        self.driver = self.driver_manager.test_caps()
        self.cv = CreditsView(self.driver)
        self._login()
        if WAIT_CREATIONS_IDLE:
            self._wait_creations_idle("before run")
        total = sum(1 for _ in case_iter())
        full_total = max(CASE_INDICES) if CASE_INDICES else SKIP_CASES + total
        logging.info("Matrix cases to run: %s", total)

        for fallback_index, item in enumerate(case_iter(), SKIP_CASES + 1):
            index, page, model, params = item
            if not CASE_INDICES:
                index = fallback_index
            title = self._case_title(page, model, params)
            logging.info("\n[%s/%s] %s", index, full_total, title)
            result = self._run_case(index, page, model, params)
            self.results.append(result)
            self._save_report()

        self._save_report()
        return self.results

    def close(self):
        if self.driver:
            self.driver.quit()

    def _login(self):
        sigin = SiginView(self.driver)
        data = sigin.read_json_data("data/account.json", "account1")
        if CREDITS_USERNAME:
            data["username"] = CREDITS_USERNAME
        if CREDITS_PASSWORD:
            data["password"] = CREDITS_PASSWORD
        time.sleep(3)
        if self._is_authenticated():
            return
        if MANUAL_LOGIN:
            logging.info(
                "Manual login mode: waiting up to %ss for browser login",
                MANUAL_LOGIN_TIMEOUT,
            )
            deadline = time.time() + MANUAL_LOGIN_TIMEOUT
            while time.time() < deadline:
                if self._is_authenticated():
                    logging.info("Manual login detected")
                    return
                time.sleep(2)
            raise RuntimeError("manual login timeout")

        for attempt in range(1, 4):
            logging.info("Login attempt %s", attempt)
            inputs_ready = self.driver.execute_script(
                """
                const inputs = Array.from(document.querySelectorAll('input'));
                return inputs.some(el => el.type === 'email' || el.name === 'email') &&
                       inputs.some(el => el.type === 'password' || el.name === 'password');
                """
            )
            if not inputs_ready:
                opened = bool(
                    self.driver.execute_script(
                        """
                        const norm = s => (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const btn = buttons.find(b => {
                          const r = b.getBoundingClientRect();
                          const st = getComputedStyle(b);
                          const text = norm(b.innerText || b.textContent);
                          return r.width > 5 && r.height > 5 &&
                                 st.display !== 'none' && st.visibility !== 'hidden' &&
                                 (text === 'log in' || text === 'login' || text === 'sign in');
                        });
                        if (!btn) return false;
                        btn.scrollIntoView({block:'center'});
                        btn.click();
                        return true;
                        """
                    )
                )
            else:
                opened = True
            if not opened:
                logging.warning("Login button was not opened")
                time.sleep(2)
                if self._is_authenticated():
                    return
                continue

            for _ in range(20):
                ready = self.driver.execute_script(
                    """
                    const inputs = Array.from(document.querySelectorAll('input'));
                    return inputs.some(el => el.type === 'email' || el.name === 'email') &&
                           inputs.some(el => el.type === 'password' || el.name === 'password');
                    """
                )
                if ready:
                    break
                time.sleep(1)
            else:
                text = self.driver.execute_script("return document.body.innerText || ''")
                logging.warning(
                    "Login inputs not found after opening. body tail=%r",
                    "\n".join(text.splitlines()[-20:])[:500],
                )
                self.driver.refresh()
                time.sleep(3)
                continue

            email_el = self.driver.execute_script(
                """
                return Array.from(document.querySelectorAll('input'))
                  .find(el => el.type === 'email' || el.name === 'email') || null;
                """
            )
            password_el = self.driver.execute_script(
                """
                return Array.from(document.querySelectorAll('input'))
                  .find(el => el.type === 'password' || el.name === 'password') || null;
                """
            )
            if not email_el or not password_el:
                continue

            for element, value in (
                (email_el, data["username"]),
                (password_el, data["password"]),
            ):
                element.click()
                element.send_keys(Keys.CONTROL, "a")
                element.send_keys(value)
                time.sleep(0.3)

            time.sleep(1)
            submitted = bool(
                self.driver.execute_script(
                    """
                    const norm = s => (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const candidates = buttons
                      .map(b => {
                        const r = b.getBoundingClientRect();
                        const st = getComputedStyle(b);
                        const text = norm(b.innerText || b.textContent);
                        return {b, r, st, text};
                      })
                      .filter(x => {
                        const b = x.b;
                        return x.r.width > 5 && x.r.height > 5 &&
                               x.st.display !== 'none' && x.st.visibility !== 'hidden' &&
                               !b.disabled && b.getAttribute('aria-disabled') !== 'true' &&
                               (x.text === 'login' || (x.text === 'log in' && x.r.top > 150) || x.text === 'sign in');
                      })
                      .sort((a, b) => {
                        const al = a.text === 'login' ? 0 : 1;
                        const bl = b.text === 'login' ? 0 : 1;
                        return al - bl || b.r.top - a.r.top;
                      });
                    const btn = candidates[0] && candidates[0].b;
                    if (!btn) return false;
                    btn.scrollIntoView({block:'center'});
                    btn.click();
                    return true;
                    """
                )
            )
            if not submitted:
                visible_buttons = self.driver.execute_script(
                    """
                    return Array.from(document.querySelectorAll('button'))
                      .filter(b => {
                        const r = b.getBoundingClientRect();
                        const st = getComputedStyle(b);
                        return r.width > 5 && r.height > 5 &&
                               st.display !== 'none' && st.visibility !== 'hidden';
                      })
                      .map(b => (b.innerText || b.textContent || '').replace(/\\s+/g, ' ').trim())
                      .filter(Boolean)
                      .slice(-10);
                    """
                )
                logging.warning(
                    "Login submit button unavailable after typing credentials. buttons=%s",
                    visible_buttons,
                )
                continue

            for _ in range(25):
                if self._is_authenticated():
                    logging.info("Login succeeded")
                    return
                time.sleep(1)
            self.driver.refresh()
            time.sleep(3)

        raise RuntimeError("login failed")

    def _is_authenticated(self):
        text = self.driver.execute_script("return document.body.innerText || ''")
        return "Log In" not in text and ("My Creations" in text or "Pro" in text)

    def _case_title(self, page, model, params):
        parts = [page["page"], model["name"]]
        for key in ("duration", "resolution", "quality", "ratio"):
            if params.get(key) and params[key] != "-":
                parts.append(params[key])
        return " / ".join(parts)

    def _base_result(self, index, page, model, params):
        return {
            "index": index,
            "page": page["page"],
            "path": page["path"],
            "model": model["name"],
            "duration": params.get("duration", "-"),
            "resolution": params.get("resolution", "-"),
            "quality": params.get("quality", "-"),
            "ratio": params.get("ratio", "-"),
            "displayed": None,
            "before": None,
            "after": None,
            "actual": None,
            "match": None,
            "status": "ERROR",
            "error": None,
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _run_case(self, index, page, model, params):
        result = self._base_result(index, page, model, params)
        try:
            self._goto(page["path"])
            if model["name"] != "-":
                selected = self._select_model_exact(model["name"])
                result["selected_model"] = selected
                if selected != model["name"]:
                    raise RuntimeError(f"model selection failed: selected={selected!r}")

            for group in ("duration", "resolution", "quality", "ratio"):
                target = params.get(group)
                if target and target != "-":
                    if not self._click_option(target):
                        raise RuntimeError(f"option not found: {group}={target}")
                    time.sleep(0.7)

            self._prepare_inputs(page["requires"])
            displayed = self._read_create_cost()
            result["displayed"] = displayed
            if not displayed:
                raise RuntimeError("create cost not found")

            before = self._wait_balance_stable()
            result["before"] = before
            if before is None:
                raise RuntimeError("balance read failed before create")

            if not self._click_create():
                raise RuntimeError("Create button unavailable")

            deduction_base, after = self._wait_deduction(before)
            if deduction_base != before:
                result["original_before"] = before
                result["before"] = deduction_base
                before = deduction_base
            result["after"] = after
            if after is None:
                raise RuntimeError("balance read failed after create")

            result["actual"] = before - after
            if result["actual"] == displayed:
                result["match"] = True
                result["status"] = "PASS"
            elif result["actual"] == 0:
                result["status"] = "NO_DEDUCTION"
                result["error"] = "balance unchanged after create"
            else:
                result["match"] = False
                result["status"] = "FAIL"

            logging.info(
                "[%s] displayed=%s actual=%s balance=%s->%s",
                result["status"],
                displayed,
                result["actual"],
                before,
                after,
            )
            if WAIT_CREATIONS_IDLE:
                self._wait_creations_idle(f"after case {index}")
                final_balance = self._wait_balance_stable(timeout=20, hits=2)
                result["final_balance"] = final_balance
                if final_balance is not None:
                    result["final_actual"] = before - final_balance
                    if final_balance != after:
                        result["post_create_balance_change"] = after - final_balance
        except Exception as exc:
            result["error"] = str(exc)[:200]
            result["status"] = "ERROR"
            logging.error("[ERROR] %s", exc)
            try:
                result["screenshot"] = self.cv.take_screenshot(
                    f"credits_error_{index}_{page['key']}"
                )
            except Exception:
                pass
        return result

    def _creations_generating_count(self):
        self.driver.get(origin(self.driver) + "/app/creations")
        time.sleep(4)
        counts = []
        for tab in ("Video", "Image"):
            self.driver.execute_script(
                """
                const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
                const target = arguments[0];
                const nodes = Array.from(document.querySelectorAll('button,a,div,span'))
                  .filter(el => norm(el.innerText || el.textContent) === target);
                if (nodes.length) {
                  const el = nodes[0].closest('button,a') || nodes[0];
                  el.scrollIntoView({block:'center'});
                  el.click();
                }
                """,
                tab,
            )
            time.sleep(1)
            text = self.driver.execute_script("return document.body.innerText || ''")
            counts.append(text.lower().count("generating"))
        return max(counts) if counts else 0

    def _wait_creations_idle(self, label):
        deadline = time.time() + CREATIONS_IDLE_TIMEOUT
        last_count = None
        while time.time() < deadline:
            count = self._creations_generating_count()
            if count == 0:
                logging.info("Creations idle: %s", label)
                return True
            if count != last_count:
                logging.info("Waiting creations idle (%s): %s generating", label, count)
                last_count = count
            time.sleep(CREATIONS_IDLE_POLL)
        raise RuntimeError(
            f"creations still generating after {CREATIONS_IDLE_TIMEOUT}s: {label}"
        )

    def _goto(self, path):
        url = origin(self.driver) + path
        self.driver.get(url)
        time.sleep(3)
        if path.split("/")[-1] not in self.driver.current_url:
            raise RuntimeError(f"navigation failed: {self.driver.current_url}")

    def _infer_model(self, text):
        text = norm_text(text)
        for model in ALL_MODELS:
            if model in text:
                return model
        return None

    def _current_selected_model(self):
        text = self.driver.execute_script(
            """
            const models = arguments[0];
            const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
            const visible = el => {
              const r = el.getBoundingClientRect();
              const st = getComputedStyle(el);
              return r.width > 20 && r.height > 20 &&
                     st.visibility !== 'hidden' && st.display !== 'none' &&
                     r.bottom > 0 && r.top < innerHeight;
            };
            const nodes = Array.from(document.querySelectorAll('button,[role="button"]'))
              .filter(visible)
              .map(el => ({el, t: norm(el.innerText || el.textContent), r: el.getBoundingClientRect()}))
              .filter(x => x.r.left < 900 && models.some(m => x.t.includes(m)) &&
                           x.r.height >= 40 && x.r.height <= 150 && x.t.length < 300)
              .sort((a,b) => a.r.top - b.r.top || a.r.left - b.r.left || a.t.length - b.t.length);
            return nodes.length ? nodes[0].t : '';
            """,
            ALL_MODELS,
        )
        return self._infer_model(text)

    def _open_model_dropdown(self):
        opened = self.driver.execute_script(
            """
            const models = arguments[0];
            const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
            const visible = el => {
              const r = el.getBoundingClientRect();
              const st = getComputedStyle(el);
              return r.width > 20 && r.height > 20 &&
                     st.visibility !== 'hidden' && st.display !== 'none' &&
                     r.bottom > 0 && r.top < innerHeight;
            };
            const nodes = Array.from(document.querySelectorAll('button,[role="button"]'))
              .filter(visible)
              .map(el => ({el, t: norm(el.innerText || el.textContent), r: el.getBoundingClientRect()}))
              .filter(x => x.r.left < 900 && models.some(m => x.t.includes(m)) &&
                           x.r.height >= 40 && x.r.height <= 150 && x.t.length < 300)
              .sort((a,b) => a.r.top - b.r.top || a.r.left - b.r.left || a.t.length - b.t.length);
            if (!nodes.length) return false;
            nodes[0].el.scrollIntoView({block:'center'});
            nodes[0].el.click();
            return true;
            """,
            ALL_MODELS,
        )
        time.sleep(0.8)
        return bool(opened)

    def _select_model_exact(self, target):
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.2)
        if self._current_selected_model() == target:
            return target

        if not self._open_model_dropdown():
            return self._current_selected_model()

        conflict = ["Nano Banana Pro"] if target == "Nano Banana" else []
        clicked = self.driver.execute_script(
            """
            const target = arguments[0];
            const conflict = arguments[1] || [];
            const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
            const visible = el => {
              const r = el.getBoundingClientRect();
              const st = getComputedStyle(el);
              return r.width > 10 && r.height > 10 &&
                     st.visibility !== 'hidden' && st.display !== 'none' &&
                     r.bottom > 0 && r.top < innerHeight;
            };
            const bad = t => conflict.some(c => t.includes(c));
            const nodes = Array.from(document.querySelectorAll('button,[role="menuitem"],[role="option"],[role="button"]'))
              .filter(visible)
              .map(el => ({el, t: norm(el.innerText || el.textContent), r: el.getBoundingClientRect(), role: el.getAttribute('role') || ''}))
              .filter(x => x.r.left < 900 && x.t.includes(target) && !bad(x.t) &&
                           x.r.height >= 24 && x.r.height <= 150 && x.t.length < 300)
              .sort((a,b) => {
                const ar = (a.role === 'menuitem' || a.role === 'option') ? 0 : 1;
                const br = (b.role === 'menuitem' || b.role === 'option') ? 0 : 1;
                const as = a.t.startsWith(target) ? 0 : 1;
                const bs = b.t.startsWith(target) ? 0 : 1;
                return ar - br || as - bs || a.t.length - b.t.length || a.r.top - b.r.top;
              });
            if (!nodes.length) return false;
            nodes[0].el.scrollIntoView({block:'center'});
            nodes[0].el.click();
            return true;
            """,
            target,
            conflict,
        )
        time.sleep(1.5)
        return self._current_selected_model() if clicked else None

    def _click_option(self, target):
        target_upper = target.upper()
        for _ in range(8):
            clicked = bool(
                self.driver.execute_script(
                    """
                    const target = arguments[0];
                    const targetUpper = arguments[1];
                    const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
                    const visible = el => {
                      const r = el.getBoundingClientRect();
                      const st = getComputedStyle(el);
                      return r.width > 4 && r.height > 4 &&
                             st.visibility !== 'hidden' && st.display !== 'none' &&
                             r.bottom > 0 && r.top < innerHeight;
                    };
                    const nodes = Array.from(document.querySelectorAll('label,button,[role="button"],[role="radio"],div,span'))
                      .filter(visible)
                      .map(el => ({el, t: norm(el.innerText || el.textContent), r: el.getBoundingClientRect()}))
                      .filter(x => x.r.left > 180 && x.r.left < 1200 && x.t.length <= 30 &&
                                   (x.t === target || x.t.toUpperCase() === targetUpper))
                      .sort((a,b) => {
                        const ae = ['LABEL','BUTTON'].includes(a.el.tagName) ? 0 : 1;
                        const be = ['LABEL','BUTTON'].includes(b.el.tagName) ? 0 : 1;
                        const as = /selected|active/i.test(a.el.className || '') ? 0 : 1;
                        const bs = /selected|active/i.test(b.el.className || '') ? 0 : 1;
                        return ae - be || as - bs || a.r.top - b.r.top || a.r.left - b.r.left;
                      });
                    if (!nodes.length) return false;
                    nodes[0].el.scrollIntoView({block:'center'});
                    nodes[0].el.click();
                    return true;
                    """,
                    target,
                    target_upper,
                )
            )
            if clicked:
                time.sleep(0.5)
                return True
            self.driver.execute_script(
                """
                const scrollers = [document.scrollingElement, ...Array.from(document.querySelectorAll('main,section,div'))]
                  .filter(Boolean)
                  .filter((el, idx, arr) => arr.indexOf(el) === idx)
                  .filter(el => el.scrollHeight > el.clientHeight + 40)
                  .filter(el => {
                    if (el === document.scrollingElement) return true;
                    const r = el.getBoundingClientRect();
                    return r.left > 180 && r.left < 1200 && r.width > 120 && r.height > 120;
                  })
                  .sort((a,b) => (b.scrollHeight-b.clientHeight) - (a.scrollHeight-a.clientHeight));
                const sc = scrollers[0] || document.scrollingElement;
                if (sc) {
                  sc.scrollTop = Math.min(
                    sc.scrollTop + Math.max(220, Math.floor(sc.clientHeight * 0.7)),
                    sc.scrollHeight
                  );
                }
                """
            )
            time.sleep(0.25)
        return False

    def _prepare_inputs(self, requirement):
        if requirement in ("image", "video"):
            filepath = TEST_IMAGE if requirement == "image" else TEST_VIDEO
            if not os.path.exists(filepath):
                raise RuntimeError(f"missing input file: {filepath}")
            if not self._upload_file(filepath):
                raise RuntimeError(f"upload failed: {filepath}")
            time.sleep(5)

        if requirement in ("image", "video", "prompt"):
            if not self._fill_prompt(DEFAULT_PROMPT):
                logging.warning("Prompt textarea was not found")
            time.sleep(1)

    def _fill_prompt(self, text):
        for textarea in self.driver.find_elements(By.CSS_SELECTOR, "textarea"):
            try:
                if not textarea.is_displayed() or not textarea.is_enabled():
                    continue
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", textarea
                )
                textarea.click()
                textarea.send_keys(Keys.CONTROL, "a")
                textarea.send_keys(text)
                self.driver.execute_script(
                    """
                    const ta = arguments[0];
                    ta.dispatchEvent(new Event('input', {bubbles: true}));
                    ta.dispatchEvent(new Event('change', {bubbles: true}));
                    """,
                    textarea,
                )
                value = textarea.get_attribute("value") or ""
                if value.strip() == text:
                    return True
            except Exception:
                continue

        return bool(
            self.driver.execute_script(
                """
                const text = arguments[0];
                const textareas = Array.from(document.querySelectorAll('textarea'))
                  .filter(ta => {
                    const r = ta.getBoundingClientRect();
                    const st = getComputedStyle(ta);
                    return r.width > 10 && r.height > 10 &&
                           st.display !== 'none' && st.visibility !== 'hidden';
                  });
                const ta = textareas[0];
                if (!ta) return false;
                const setter = Object.getOwnPropertyDescriptor(
                  window.HTMLTextAreaElement.prototype, 'value'
                ).set;
                setter.call(ta, text);
                ta.dispatchEvent(new Event('input', {bubbles: true}));
                ta.dispatchEvent(new Event('change', {bubbles: true}));
                return (ta.value || '').trim() === text;
                """,
                text,
            )
        )

    def _upload_file(self, filepath):
        self.driver.execute_script(
            """
            for (const input of document.querySelectorAll('input[type="file"]')) {
              input.style.display = 'block';
              input.style.visibility = 'visible';
              input.style.opacity = '1';
              input.removeAttribute('hidden');
            }
            """
        )
        inputs = self.driver.find_elements("css selector", 'input[type="file"]')
        for input_el in inputs:
            try:
                input_el.send_keys(os.path.abspath(filepath))
                return True
            except Exception:
                continue
        return False

    def _read_create_cost(self):
        return self.driver.execute_script(
            """
            const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
            const buttons = Array.from(document.querySelectorAll('button'));
            for (const b of buttons) {
              const r = b.getBoundingClientRect();
              const st = getComputedStyle(b);
              if (r.width <= 5 || r.height <= 5 ||
                  st.display === 'none' || st.visibility === 'hidden') continue;
              const text = norm(b.innerText || b.textContent);
              if (/^create\\b/i.test(text) && !/creation/i.test(text)) {
                const nums = text.match(/\\d+/);
                if (nums) return parseInt(nums[0], 10);
              }
            }
            return null;
            """
        )

    def _click_create(self):
        for _ in range(20):
            result = self.driver.execute_script(
                """
                const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
                    const buttons = Array.from(document.querySelectorAll('button'));
                    for (const b of buttons) {
                      const r = b.getBoundingClientRect();
                      const st = getComputedStyle(b);
                      if (r.width <= 5 || r.height <= 5 ||
                          st.display === 'none' || st.visibility === 'hidden') continue;
                      const text = norm(b.innerText || b.textContent).toLowerCase();
                      const cls = String(b.className || '');
                      if (text.startsWith('create') && !text.includes('creation')) {
                        b.scrollIntoView({block:'center'});
                        if (b.disabled || b.getAttribute('aria-disabled') === 'true' ||
                            /generate-button--disabled/.test(cls)) return 'disabled';
                        b.click();
                        return 'ok';
                      }
                    }
                return 'not-found';
                """
            )
            if result == "ok":
                self._confirm_compliance_if_present()
                return True
            time.sleep(1)
        return False

    def _confirm_compliance_if_present(self):
        for _ in range(20):
            clicked = bool(
                self.driver.execute_script(
                    """
                    const norm = s => (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const btn = buttons.find(b => {
                      const r = b.getBoundingClientRect();
                      const st = getComputedStyle(b);
                      const text = norm(b.innerText || b.textContent);
                      return r.width > 5 && r.height > 5 &&
                             st.display !== 'none' && st.visibility !== 'hidden' &&
                             !b.disabled && b.getAttribute('aria-disabled') !== 'true' &&
                             (text === 'confirm & use' || text === 'confirm and use');
                    });
                    if (!btn) return false;
                    btn.scrollIntoView({block:'center'});
                    btn.click();
                    return true;
                    """
                )
            )
            if clicked:
                logging.info("Compliance confirmation accepted")
                time.sleep(1.5)
                return True
            time.sleep(0.5)
        return False

    def _wait_balance_stable(self, timeout=25, hits=3):
        last = None
        same = 0
        deadline = time.time() + timeout
        fallback = None
        while time.time() < deadline:
            current = self.cv.get_credit_balance()
            if current is not None:
                fallback = current
                if current == last:
                    same += 1
                    if same >= hits:
                        return current
                else:
                    same = 1
                    last = current
            time.sleep(2)
        return fallback

    def _wait_deduction(self, before):
        deadline = time.time() + WAIT_DEDUCTION_SECONDS
        base = before
        fallback = before
        while time.time() < deadline:
            time.sleep(2)
            current = self.cv.get_credit_balance()
            if current is None:
                continue
            fallback = current
            if current > base:
                base = current
            elif current < base:
                return base, current
        return base, fallback

    def _save_report(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        json_path = os.path.join(OUTPUT_DIR, "credits_report.json")
        html_path = os.path.join(OUTPUT_DIR, "credits_report.html")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self._render_html())
        logging.info("Report saved: %s", html_path)

    def _render_html(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        no_deduction = sum(1 for r in self.results if r["status"] == "NO_DEDUCTION")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        rows = []
        for item in self.results:
            status_class = {
                "PASS": "pass",
                "FAIL": "fail",
                "NO_DEDUCTION": "warn",
                "ERROR": "err",
            }.get(item["status"], "")
            rows.append(
                "<tr>"
                f"<td>{item['index']}</td>"
                f"<td>{html.escape(item['page'])}</td>"
                f"<td>{html.escape(item['model'])}</td>"
                f"<td>{html.escape(item.get('duration') or '-')}</td>"
                f"<td>{html.escape(item.get('resolution') or '-')}</td>"
                f"<td>{html.escape(item.get('quality') or '-')}</td>"
                f"<td>{html.escape(item.get('ratio') or '-')}</td>"
                f"<td class='num'>{item['displayed'] if item['displayed'] is not None else '-'}</td>"
                f"<td class='num'>{item['actual'] if item['actual'] is not None else '-'}</td>"
                f"<td class='num'>{item['before'] if item['before'] is not None else '-'}</td>"
                f"<td class='num'>{item['after'] if item['after'] is not None else '-'}</td>"
                f"<td class='{status_class}'>{html.escape(item['status'])}</td>"
                f"<td>{html.escape(item.get('error') or '')}</td>"
                "</tr>"
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Credits Deduction Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; background: #f6f7f9; color: #222; }}
    h1 {{ margin: 0 0 16px; }}
    .summary {{ display: flex; gap: 16px; margin-bottom: 18px; flex-wrap: wrap; }}
    .box {{ background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 10px 14px; min-width: 110px; }}
    .box b {{ display: block; font-size: 24px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    th {{ background: #222; color: #fff; text-align: left; padding: 8px; font-size: 12px; }}
    td {{ border-bottom: 1px solid #eee; padding: 7px 8px; font-size: 12px; vertical-align: top; }}
    .num {{ text-align: right; }}
    .pass {{ color: #0a7a28; font-weight: 700; }}
    .fail {{ color: #b00020; font-weight: 700; }}
    .warn {{ color: #b36b00; font-weight: 700; }}
    .err {{ color: #a00000; font-weight: 700; }}
    .footer {{ color: #777; margin-top: 14px; font-size: 12px; }}
  </style>
</head>
<body>
  <h1>Credits Deduction Report</h1>
  <div class="summary">
    <div class="box"><b>{total}</b>Total</div>
    <div class="box"><b class="pass">{passed}</b>PASS</div>
    <div class="box"><b class="fail">{failed}</b>FAIL</div>
    <div class="box"><b class="warn">{no_deduction}</b>No deduction</div>
    <div class="box"><b class="err">{errors}</b>Error</div>
  </div>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Page</th><th>Model</th><th>Duration</th><th>Resolution</th>
        <th>Quality</th><th>Ratio</th><th>Displayed</th><th>Actual</th>
        <th>Before</th><th>After</th><th>Status</th><th>Note</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  <div class="footer">Generated at {now}. AI NSFW excluded by request.</div>
</body>
</html>"""


def main():
    runner = CreditMatrixRunner()
    try:
        runner.run()
    finally:
        runner.close()

    failed = [r for r in runner.results if r["status"] != "PASS"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
