import datetime
import logging.handlers
import os
import re
import time
from stat import ST_MTIME


class HourRotationFileHandler(logging.handlers.BaseRotatingHandler):

    def __init__(
        self,
        filename: str,
        interval=1,
        unit: str = "hour",
        backupCount=0,
        utc=False,
        encoding=None,
        delay=False,
        errors=None,
    ):
        """

        :param filename: 日志文件名
        :param interval: 两次输出日志的间隔
        :param unit: 单位
        :param backupCount: 最多保留日志文件数量
        :param utc: 日志名称的时间部分是否使用 utc 时区格式
        :param encoding: 日志文件的编码
        :param delay:
        :param errors:
        """
        logging.FileHandler.__init__(self, filename, "a", encoding, delay, errors)
        self.backupCount = backupCount
        self.unit = unit.lower()
        # second
        if self.unit == "second":
            self.interval = 1
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(\.\w+)?$"
        # minute
        elif self.unit == "minute":
            self.interval = 60
            self.suffix = "%Y-%m-%d_%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(\.\w+)?$"
        # hour
        elif self.unit == "hour":
            self.interval = 60 * 60
            self.suffix = "%Y-%m-%d_%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}(\.\w+)?$"
        # day
        elif self.unit == "day":
            self.interval = 60 * 60 * 24
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.unit)

        self.extMatch = re.compile(self.extMatch, re.ASCII)
        self.interval = self.interval * interval
        self.utc = utc

        # 获取当前时区的本地时间
        local_now = datetime.datetime.now(datetime.timezone.utc).astimezone()
        # 获取本地时间相对于UTC的偏移量
        self.tz_offset = local_now.utcoffset().total_seconds()

        filename = self.baseFilename
        if os.path.exists(filename):
            # 文件上次修改时间
            t = os.stat(filename)[ST_MTIME]
        else:
            t = int(time.time())
        
        # 计算下次该分离的时间
        self.rolloverAt = self.computeRollover(t)

    def computeRollover(self, currentTime):
        """
        计算下次需要分离的时间
        """
        # 计算当前所在的间隔区间 [startTime, endTime)
        if self.unit == 'day':
            # 一天的开始应该是0点
            startTime = currentTime - (currentTime % self.interval) - self.tz_offset
        else:
            startTime = currentTime - (currentTime % self.interval)
        endTime = startTime + self.interval
        return endTime

    def shouldRollover(self, record):
        """
        判断是否需要分离
        """
        t = int(time.time())
        if t >= self.rolloverAt:
            # 目标日志文件不是一个文件，选择不写入
            if os.path.exists(self.baseFilename) and not os.path.isfile(
                self.baseFilename
            ):
                self.rolloverAt = self.computeRollover(t)
                return False

            return True
        return False

    def getFilesToDelete(self):
        """
        当文件分离时，需要删除的日志文件
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        n, e = os.path.splitext(baseName)
        prefix = n + "."
        plen = len(prefix)
        for fileName in fileNames:
            if self.namer is None:
                # Our files will always start with baseName
                if not fileName.startswith(baseName):
                    continue
            else:
                # Our files could be just about anything after custom naming, but
                # likely candidates are of the form
                # foo.log.DATETIME_SUFFIX or foo.DATETIME_SUFFIX.log
                if (
                    not fileName.startswith(baseName)
                    and fileName.endswith(e)
                    and len(fileName) > (plen + 1)
                    and not fileName[plen + 1].isdigit()
                ):
                    continue

            if fileName[:plen] == prefix:
                suffix = fileName[plen:]
                # See bpo-45628: The date/time suffix could be anywhere in the
                # filename
                parts = suffix.split(".")
                for part in parts:
                    if self.extMatch.match(part):
                        result.append(os.path.join(dirName, fileName))
                        break
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[: len(result) - self.backupCount]
        return result

    def doRollover(self):
        # 关闭当前流
        if self.stream:
            self.stream.close()
            self.stream = None

        # 时间
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]

        # 左区间的端点
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)

        # 创建替换的文件，替换当前的文件
        dfn = self.rotation_filename(
            self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        )
        if os.path.exists(dfn):
            os.remove(dfn)
        self.rotate(self.baseFilename, dfn)

        # 删除多的日志文件
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)

        if not self.delay:
            self.stream = self._open()

        # 计算新的切换时间
        newRolloverAt = self.computeRollover(currentTime)

        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval

        # If DST changes and midnight or weekly rollover, adjust for this.
        if not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if (
                    not dstNow
                ):  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend

        self.rolloverAt = newRolloverAt
