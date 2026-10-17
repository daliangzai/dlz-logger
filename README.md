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

- 字符串：`"DEBUG"`、`"INFO"`、`"WARNING"`、`"ERROR"`、`"CRITICAL"`
- 整数：如标准库 `logging.DEBUG`

## 功能特性

- 控制台彩色输出
- 按天轮转文件日志
- 自动推断调用方模块名
- 同时支持函数式和类式调用
