# project
from config_data.config import config
from database.connector import PostgresConnector as pg
from service.openrouter import openrouter_client

# misc
import asyncio
import logging

logger = logging.getLogger(__name__)


async def replenish_loop():
    '''
    Раз в poll_interval_sec проходит по всем set'ам, у которых задан
    generator_prompt и target_pool_size > 0, и догенерирует вопросы
    в очередь, пока в pending их не станет >= target_pool_size.

    На один проход одного set'а делает не больше config.generator.batch_size
    запросов, чтобы не вылетать по rate-limit'у.
    '''
    interval = config.generator.poll_interval_sec
    batch = config.generator.batch_size

    logger.info(f'Generator worker запущен, интервал {interval}с, batch {batch}')

    while True:
        try:
            await replenish_once(batch_size = batch)
        except Exception as e:
            logger.error(f'replenish_once упал: {e}')

        await asyncio.sleep(interval)


async def replenish_once(batch_size: int = 3) -> int:
    '''
    Один проход. Возвращает число сгенерированных вопросов.
    '''
    sets_ = pg.get_generator_sets()
    if not sets_:
        return 0

    generated = 0

    for set_id, account_id, set_name, prompt, model, target in sets_:
        pending = pg.queue_pending_count(set_id)
        deficit = target - pending
        if deficit <= 0:
            continue

        logger.info(f'set "{set_name}" (id={set_id}): '
                    f'pending={pending}, target={target}, '
                    f'будем генерить до {min(deficit, batch_size)} штук')

        for _ in range(min(deficit, batch_size)):
            payload = await openrouter_client.generate_question(
                topic_prompt = prompt,
                model = model
            )
            if not payload:
                break

            try:
                pg.queue_push(
                    set_id = set_id,
                    account_id = account_id,
                    payload = payload,
                    model = model or config.openrouter.default_model
                )
                generated += 1
                logger.info(f'set "{set_name}": +1 в очередь '
                            f'({payload.get("question", "")[:80]}...)')
            except Exception as e:
                logger.error(f'queue_push failed: {e}')
                break

    return generated
