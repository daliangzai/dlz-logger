# dlz-logger

`dlz-logger` 是一个轻量级彩色日志库，支持控制台着色输出，以及按天切分的文件日志。

## 安装

```bash
pip install dlz-logger
```

## 推荐调用方式

现在可以直接省略 `__name__`：

```python
from datetime import datetime
from dlz_logger import get_logger

LOG_LEVEL = "DEBUG"

logger = get_logger(
    log_level=LOG_LEVEL,
    save=True,
    file_name=f"abcd-{datetime.now():%Y%m%d_%H%M%S}",
)

logger.info("开始")
```

## 类式调用

```python
from dlz_logger import LOGGER

logger = LOGGER(
    log_level="INFO",
    save=True,
    file_name="demo"
)

logger.info("hello")
```

如果你需要原生 `logging.Logger`，也仍然可以继续调用：

```python
logger = LOGGER(log_level="INFO").get_logger()
```

## 日志级别

`log_level` 支持两种写法：

- 字符串：如 `"DEBUG"`、`"SUCCESS"`
- 整数：如标准库 `logging.DEBUG`

内置级别刻度（小 → 大）：

| 级别 | 数值 | 颜色 | 说明 |
| --- | --- | --- | --- |
| `TRACE` | 5 | 暗灰 | 比 DEBUG 更细，排查疑难杂症时才打开 |
| `DEBUG` | 10 | 蓝 | 调试信息 |
| `INFO` | 20 | 灰 | 常规信息 |
| `NOTICE` | 22 | 青 | 正常但值得知道的事件（启动完成、配置加载） |
| `SUCCESS` | 25 | 绿 | 操作成功 |
| `WARNING` | 30 | 黄 | 警告 |
| `RETRY` | 35 | 橙 | 临时故障正在重试 |
| `ERROR` | 40 | 亮红 | 错误 |
| `FAIL` | 45 | 粉红 | 失败但不致命 |
| `CRITICAL` | 50 | 红 | 严重错误 |
| `AUDIT` | 55 | 紫 | 审计日志（登录、权限变更等敏感操作） |
| `ANNOUNCEMENT` | 60 | 蓝 | 重要公告，任何 `log_level` 下都会输出 |
| `METRIC` | 65 | 白 | 打点数据，方便采集器按级别名抓取 |

除 `DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL` 外均为扩展级别，直接调用同名方法即可：

```python
from dlz_logger import get_logger, TRACE

logger = get_logger(log_level="NOTICE")

logger.trace("函数 enter，args=()")       # 暗灰
logger.notice("服务启动完成")             # 青色
logger.success("任务执行成功")            # 绿色
logger.retry("请求超时，1s 后重试第 1 次")  # 橙色
logger.fail("校验失败，但流程继续")        # 粉红
logger.audit("admin 登录成功")            # 紫色
logger.announcement("系统将于今晚停机维护")  # 蓝色，永不被过滤
logger.metric("elapsed_ms=42")           # 白色
```

级别数值也可以直接从 `dlz_logger` 导入（`TRACE`、`NOTICE`、`SUCCESS`、`RETRY`、`FAIL`、`AUDIT`、`ANNOUNCEMENT`、`METRIC`），或从 `dlz_logger.CUSTOM_LEVELS` 拿到完整映射。

## 功能特性

- 控制台彩色输出
- 8 个扩展日志级别，覆盖 DEBUG~CRITICAL 之间的语义空白
- 按天轮转文件日志
- 自动推断调用方模块名
- 同时支持函数式和类式调用
