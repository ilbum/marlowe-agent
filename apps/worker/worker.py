import arq.connections

from apps.worker.tasks.extraction_task import process_item_batch
from apps.worker.tasks.planner_task import plan_investigation
from apps.worker.tasks.traversal_task import traverse_list_pages
from packages.config import settings


class WorkerSettings:
    redis_settings = arq.connections.RedisSettings.from_dsn(settings.redis_url)
    functions = [plan_investigation, traverse_list_pages, process_item_batch]
    max_jobs = 10
    job_timeout = 3600


if __name__ == "__main__":
    import asyncio
    from arq import run_worker
    run_worker(WorkerSettings)
