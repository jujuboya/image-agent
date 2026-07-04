# -*- coding: utf-8 -*-
"""
消息队列服务
支持RabbitMQ和本地队列
"""

import asyncio
import json
from typing import Callable, Any, Optional

from config import settings

import logging

logger = logging.getLogger(__name__)


class QueueService:
    """消息队列服务"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self._local_queue = asyncio.Queue()
        self._use_local = False
        self._handlers = {}

    async def connect(self):
        """连接消息队列"""
        try:
            import aio_pika
            self.connection = await aio_pika.connect_robust(
                settings.get_rabbitmq_url,
                heartbeat=600,
            )
            self.channel = await self.connection.channel()
            logger.info("RabbitMQ连接成功")
        except Exception as e:
            logger.warning(f"RabbitMQ连接失败: {e}，使用本地队列")
            self._use_local = True

    async def close(self):
        """关闭连接"""
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ连接已关闭")

    async def declare_queue(self, queue_name: str):
        """声明队列"""
        if not self._use_local and self.channel:
            await self.channel.declare_queue(queue_name, durable=True)

    async def publish(self, queue_name: str, message: dict):
        """
        发布消息

        Args:
            queue_name: 队列名称
            message: 消息内容
        """
        if self._use_local:
            await self._local_queue.put({
                'queue': queue_name,
                'data': message
            })
            logger.debug(f"消息已加入本地队列: {queue_name}")
        else:
            import aio_pika
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message, ensure_ascii=False).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue_name,
            )
            logger.debug(f"消息已发布到RabbitMQ: {queue_name}")

    async def consume(self, queue_name: str, handler: Callable):
        """
        消费消息

        Args:
            queue_name: 队列名称
            handler: 消息处理函数
        """
        self._handlers[queue_name] = handler

        if self._use_local:
            # 本地队列消费
            asyncio.create_task(self._consume_local(queue_name, handler))
        else:
            # RabbitMQ消费
            queue = await self.channel.declare_queue(queue_name, durable=True)
            await queue.consume(lambda message: self._handle_message(message, handler))

    async def _consume_local(self, queue_name: str, handler: Callable):
        """本地队列消费"""
        while True:
            try:
                item = await self._local_queue.get()
                if item['queue'] == queue_name:
                    await handler(item['data'])
                self._local_queue.task_done()
            except Exception as e:
                logger.error(f"本地队列消费错误: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, message, handler: Callable):
        """处理RabbitMQ消息"""
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                await handler(data)
            except Exception as e:
                logger.error(f"消息处理错误: {e}")


class TaskQueue:
    """任务队列（简化版，用于异步任务）"""

    def __init__(self, max_workers: int = 4):
        self.queue = asyncio.Queue()
        self.max_workers = max_workers
        self._workers = []
        self._running = False

    async def start(self):
        """启动工作线程"""
        self._running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
        logger.info(f"任务队列已启动，工作线程数: {self.max_workers}")

    async def stop(self):
        """停止工作线程"""
        self._running = False
        # 等待队列清空
        await self.queue.join()
        # 取消工作线程
        for worker in self._workers:
            worker.cancel()
        logger.info("任务队列已停止")

    async def _worker(self, name: str):
        """工作线程"""
        logger.info(f"工作线程 {name} 已启动")
        while self._running:
            try:
                task_func, args, kwargs, future = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )
                try:
                    result = await task_func(*args, **kwargs)
                    if not future.done():
                        future.set_result(result)
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                finally:
                    self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"工作线程 {name} 错误: {e}")

    async def submit(self, task_func: Callable, *args, **kwargs) -> Any:
        """
        提交任务

        Args:
            task_func: 任务函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            任务结果
        """
        future = asyncio.get_event_loop().create_future()
        await self.queue.put((task_func, args, kwargs, future))
        return await future

    def submit_nowait(self, task_func: Callable, *args, **kwargs):
        """
        提交任务（不等待）

        Args:
            task_func: 任务函数
            *args: 位置参数
            **kwargs: 关键字参数
        """
        future = asyncio.get_event_loop().create_future()
        self.queue.put_nowait((task_func, args, kwargs, future))
        return future


# 全局任务队列实例
task_queue = TaskQueue()
