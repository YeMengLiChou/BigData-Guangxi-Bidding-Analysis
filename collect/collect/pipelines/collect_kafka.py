import logging

from collect.collect.utils import log

logger = logging.getLogger(__name__)


class CollectKafkaPipeline:

    def process_item(self, item, spider):
        log.json(logger.debug, item)
        return item
