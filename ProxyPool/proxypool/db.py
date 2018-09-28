import redis
from proxypool.error import PoolEmptyError
from proxypool.setting import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_KEY
from proxypool.setting import MAX_SCORE, MIN_SCORE, INITIAL_SCORE
from random import choice
import re


class RedisClient(object):
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD):
        """
        初始化
        decode_responses=True: 写入的键值对中的value为str类型，不加这个参数写入的则为字节类型
        """
        self.db = redis.StrictRedis(host=host, port=port, password=password, decode_responses=True)
    
    def add(self, proxy, score=INITIAL_SCORE):
        """
        添加代理，初始分数为10
        Redis ZSCORE命令返回成员的有序集合在键中的比分。如果成员没有在排序集合存在，或键不存在，则返回nil
        Redis Zadd 命令用于将一个或多个成员元素及其分数值加入到有序集当中
        redis 127.0.0.1:6379> ZADD myzset 1 b 2 c 3 d 4 e
        (integer) 4
        redis 127.0.0.1:6379> ZSCORE myzset "c"
        (integer) 3
        redis 127.0.0.1:6379> ZSCORE myzset "y"
        (nil)
        """
        if not re.match('\d+\.\d+\.\d+\.\d+\:\d+', proxy):
            print('代理不符合规范', proxy, '丢弃')
            return
        if not self.db.zscore(REDIS_KEY, proxy):
            return self.db.zadd(REDIS_KEY, score, proxy)
    
    def random(self):
        """
        随机获取有效代理，首先尝试获取最高分数代理，如果不存在，按照排名获取，否则异常
        Zrangebyscore 返回有序集合中指定分数区间的成员列表。有序集成员按分数值递增(从小到大)次序排列。具有相同分数值的成员按字典序来排列
        Zrevrange 返回有序集中，指定区间内的成员。其中成员的位置按分数值递减(从大到小)来排列。具有相同分数值的成员按字典序的逆序排列
        """
        result = self.db.zrangebyscore(REDIS_KEY, MAX_SCORE, MAX_SCORE)
        if len(result):
            return choice(result)
        else:
            result = self.db.zrevrange(REDIS_KEY, 0, 100)
            if len(result):
                return choice(result)
            else:
                raise PoolEmptyError
    
    def decrease(self, proxy):
        """
        代理值减一分，小于最小值则删除
        zincrby('grade', 'bob', -2): 键为grade的zset中bob的分数减2
        zrem ('grade', 'mike'): 从键为grade的zset中删除mike
        """
        score = self.db.zscore(REDIS_KEY, proxy)
        if score and score > MIN_SCORE:
            print('代理', proxy, '当前分数', score, '减1')
            return self.db.zincrby(REDIS_KEY, proxy, -1)
        else:
            print('代理', proxy, '当前分数', score, '移除')
            return self.db.zrem(REDIS_KEY, proxy)
    
    def exists(self, proxy):
        """
        判断是否存在
        """
        return not self.db.zscore(REDIS_KEY, proxy) == None
    
    def max(self, proxy):
        """
        将代理设置为MAX_SCORE
        """
        print('代理', proxy, '可用，设置为', MAX_SCORE)
        return self.db.zadd(REDIS_KEY, MAX_SCORE, proxy)
    
    def count(self):
        """
        获取数量
        zcard(name): 返回键为name的zset的元素个数
        """
        return self.db.zcard(REDIS_KEY)
    
    def all(self):
        """
        获取全部代理
        zrangebyscore('grade',80,90): 返回键为grade的有序集合中80到90分的学生,按分数从低到高的顺序
        """
        return self.db.zrangebyscore(REDIS_KEY, MIN_SCORE, MAX_SCORE)
    
    def batch(self, start, stop):
        """
        批量获取
        zrevrange('grade', 0, 3): 返回键为grade的有序集合中的前四名学生，按分数从高到低
        """
        return self.db.zrevrange(REDIS_KEY, start, stop - 1)


if __name__ == '__main__':
    conn = RedisClient()
    result = conn.batch(680, 688)
    print(result)
