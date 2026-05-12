"""Пересчёт всех эмбеддингов"""
import json
from sigmaprice.matcher.config import MatcherConfig, DEFAULT_CONFIG
from sigmaprice.matcher.factory import get_embedding_provider
from sigmaprice.core.logger import get_logger
from sigmaprice.core.database import get_session
from sigmaprice.db.models import CatalogItem, ItemEmbedding

logger = get_logger(__name__)


def rebuild_all_embeddings(config: MatcherConfig | None = None):
    """Пересчитывает все эмбеддинги товаров в каталоге."""
    if config is None:
        config = DEFAULT_CONFIG

    logger.info(f"Начало пересчёта эмбеддингов, модель: {config.embedding_model}")

    provider = get_embedding_provider(config)
    session = get_session()

    try:
        session.query(ItemEmbedding).delete()
        session.commit()
        logger.info("Очищена таблица item_embeddings")
    except Exception as e:
        logger.error(f"Ошибка очистки эмбеддингов: {e}")
        session.rollback()
        return

    items = session.query(CatalogItem).all()
    logger.info(f"Найдено {len(items)} товаров для пересчёта")

    count = 0
    for item in items:
        try:
            embedding = provider.generate(item.name)
            emb = ItemEmbedding(
                catalog_item_id=item.id,
                embedding=json.dumps(embedding),
                model_version=config.embedding_model
            )
            session.add(emb)
            count += 1

            if count % 100 == 0:
                session.commit()
                logger.info(f"Обработано {count}/{len(items)}")

        except Exception as e:
            logger.error(f"Ошибка генерации эмбеддинга для {item.name}: {e}")
            continue

    session.commit()
    logger.info(f"Пересчитано {count} эмбеддингов")


if __name__ == "__main__":
    rebuild_all_embeddings()