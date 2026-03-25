import logging
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.common_fun import ReportManager  # noqa: E402

logger = logging.getLogger(__name__)


def test_report():
    """主测试报告方法"""
    logger.info("=== 开始测试报告流程 ===")

    try:
        logger.info("1. 创建报告管理器...")
        report_manager = ReportManager()

        logger.info("2. 设置测试套件...")
        suite = report_manager.setup_test_suite()

        logger.info("3. 创建测试运行器...")
        runner = report_manager.create_test_runner(suite)

        logger.info("4. 运行测试...")
        test_success = False
        try:
            run_result = report_manager.run_tests(runner)
            logger.info("4.1 测试运行完成")
            test_success = bool(run_result is not None and report_manager.last_run_success)
        except Exception as e:
            logger.error(f"4.1 测试运行失败: {str(e)}")
            test_success = False

        logger.info("5. 在HTML报告中添加运行日志...")
        try:
            report_manager.enhance_report_with_logs()
            logger.info("5.1 运行日志添加完成")
        except Exception as e:
            logger.error(f"5.1 运行日志添加失败: {str(e)}")

        logger.info("6. 开始加载邮件配置...")
        try:
            email_config = report_manager.load_email_config()
            logger.info("6.1 邮件配置加载完成")
        except Exception as e:
            logger.error(f"6.1 邮件配置加载失败: {str(e)}")
            email_config = None

        logger.info(f"测试状态: {'成功' if test_success else '失败'}")

        logger.info("7. 开始发送邮件...")
        email_sent = False
        try:
            if email_config:
                report_manager.send_test_email_only(runner, email_config)
                logger.info("7.1 邮件发送完成")
                email_sent = True
            else:
                logger.warning("7.1 跳过邮件发送（配置加载失败）")
        except Exception as e:
            logger.error(f"7.1 邮件发送失败: {str(e)}")

        logger.info("8. 开始发送企业微信推送...")
        wechat_sent = False
        try:
            success = report_manager.send_wechat_notification_standalone()
            if success:
                logger.info("8.1 企业微信推送完成")
                wechat_sent = True
            else:
                logger.error("8.1 企业微信推送失败")
        except Exception as e:
            logger.error(f"8.1 企业微信推送失败: {str(e)}")

        logger.info(f"通知发送状态 - 邮件: {'✅' if email_sent else '❌'}, 企微: {'✅' if wechat_sent else '❌'}")
        logger.info("=== 测试报告流程完成 ===")

    except Exception as e:
        logger.error(f"测试报告流程发生错误: {str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")


if __name__ == '__main__':
    test_report()
