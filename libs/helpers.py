import asyncio
import contextlib
import logging
import signal

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional


async def shutdown(
    loop: asyncio.AbstractEventLoop, executor: ThreadPoolExecutor, signal: Optional[signal.Signals] = None
) -> None:
    """Cleanup tasks tied to the service's shutdown."""

    if signal:
        logging.info(f"Received exit signal {signal.name}...")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    [task.cancel() for task in tasks]

    logging.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)

    logging.info("Shutting down executor")
    executor.shutdown(wait=False)
    logging.info(f"Releasing {len(executor._threads)} threads from executor")
    for thread in executor._threads:
        with contextlib.suppress(Exception):
            thread._tstate_lock.release()  # type: ignore

    logging.info("Stoping loop")
    loop.stop()


def handle_exception(executor: ThreadPoolExecutor, loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
    # context["message"] will always be there; but context["exception"] may not
    msg = context.get("exception", context["message"])
    logging.error(f"Caught exception: {msg}")
    logging.info("Shutting down...")
    asyncio.create_task(shutdown(loop, executor))
