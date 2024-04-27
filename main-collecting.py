from collect import run
from utils import redis_tools

if __name__ == '__main__':
    redis_tools.clear_cached_data()
    run.start(
        spider_name='bidding',
        module_path='collect.collect.settings'
    )
