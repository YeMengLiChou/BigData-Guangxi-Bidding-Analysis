import logging
import types
from concurrent.futures import ThreadPoolExecutor

__all__ = ["timeout"]

logger = logging.getLogger(__name__)


class FunctionTimeout(TimeoutError):
    pass


import concurrent.futures
import time


#
def timeout(seconds: int, record_running_time=True):
    if seconds < 0:
        raise ValueError("seconds value should be positive")

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            if record_running_time:
                logger.info(f"func {func.__name__} start recording....")

            with concurrent.futures.ThreadPoolExecutor() as executor:

                def translate():
                    res = func(*args, **kwargs)
                    if isinstance(res, types.GeneratorType):
                        return list(res)
                    else:
                        return res

                # 提交任务并设置超时时间
                future = executor.submit(translate)
                try:
                    result = future.result(timeout=seconds)  # 设置超时时间为 5 秒
                except concurrent.futures.TimeoutError:
                    future.cancel()
                    raise FunctionTimeout(
                        f"Function {func.__name__} timed out, total: {time.time() - start_time}s"
                    )
                else:
                    if record_running_time:
                        logger.info(
                            f"func {func.__name__} cost {time.time() - start_time}s <= {seconds}s!"
                        )
                    return result

        return wrapper

    return decorator


@timeout(1)
def run():
    cnt = 0
    while cnt < 5:
        time.sleep(2)
        cnt += 1
    yield cnt


if __name__ == "__main__":
    for i in run():
        print(i)
    # print(run())
