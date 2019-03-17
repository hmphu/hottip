import itertools
import json
import logging
from enum import Enum

from django.db import models
from django.utils import timezone

from . import fields, services

logger = logging.getLogger(__name__)


class Tip(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    enable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'id:{self.id},title:{self.title}'


class Channel(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tips = models.ManyToManyField(Tip, through='Assignment')

    def __str__(self):
        return f'id:{self.id},name:{self.name}'

    def take_tips(self, count):
        """通知するtipsを指定件数取得する

        過去の履歴の中でまだ使っていないTipsを取得する
        """

        assigns = self.assignment_set.filter(tip__enable=True)

        # 取得対象tips数分の過去を取得して利用済みidを取得
        logs = DistributedLog.recent_logs_by_channel(self.id, len(assigns))
        recent_assign_ids = set( log.assignment.id for log in logs )

        # 利用済みではない範囲でtipsを取得
        candidates = list(assigns.exclude(pk__in=recent_assign_ids) \
                .order_by('id')[:count])

        # 必要数に足りなければ、不足分を取得
        candidate_size = len(candidates)
        if candidate_size < count:
            adds_size = count - candidate_size
            adds = list(assigns.exclude(pk__in=[a.id for a in candidates]) \
                    .order_by('id')[:adds_size])
            candidates = candidates + adds

        tips = [a.tip for a in candidates]
        return (tips, candidates)


    class Meta:
        unique_together = (('name', ), )


class Assignment(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE)
    power = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('tip', 'channel', ), )

    def __str__(self):
        return f'id:{self.id},channel_id:{self.channel_id},tip_id:{self.tip_id}'


class DistributedLog(models.Model):
    assignment = models.ForeignKey('hottip.Assignment', on_delete=models.CASCADE)
    distributed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'id:{self.id},assignment:"{self.assignment}",distributed_at:{self.distributed_at}'

    @staticmethod
    def recent_logs_by_channel(channel_id, count):
        logs = DistributedLog.objects \
            .filter(assignment__channel=channel_id) \
            .order_by('-distributed_at')

        return logs[:count]

    @staticmethod
    def record_logs(assignments):
        DistributedLog.objects.bulk_create([
            DistributedLog(assignment=a) for a in assignments
        ])


class Distributor(models.Model):
    class Type(Enum):
        EMAIL = 'Email'
        SLACK = 'Slack'
        WEBHOOK = 'Webhook'

        @classmethod
        def choices(cls):
            return [(m.name, m.value) for m in cls]

    schedule = fields.JsonField(default={
        'month': '*', 'day': 1, 'day_of_week': '*', 'hour': '*', 'minute': '*'
    })
    type = models.CharField(max_length=200, choices=Type.choices())
    attribute = fields.JsonField(default={})
    tips_count = models.IntegerField(default=1)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def attribute_json(self):
        if self.attribute:
            try:
                return json.loads(self.attribute)
            except json.decoder.JSONDecodeError as err:
                logger.error("Invalid attribute json format: '%s'. %s", self.attribute, err)

        return {}


    def distribute(self):
        channel = self.channel
        (tips, assigns) = channel.take_tips(self.tips_count)

        logger.info(f'channel : {vars(channel)}')
        logger.info(f'tips : {tips}')
        logger.info(f'assigns : {assigns}')

        if tips:
            self.__do_distribute(tips)
            DistributedLog.record_logs(assigns)


    def __do_distribute(self, tips):
        attr_json = self.attribute_json()

        if self.type == self.Type.EMAIL:
            services.post_email(
                attr_json['email'],
                attr_json['subject'],
                tips
            )

        elif self.type == self.Type.SLACK:
            services.post_slack(
                attr_json['channel'],
                attr_json['username'],
                attr_json['icon'],
                tips
            )

        elif self.type == self.Type.WEBHOOK:
            services.post_webhook(
                attr_json['webhook_url'],
                tips
            )

        else:
            logger.error('Invalid distribution type: [%s]', self.type)
            raise RuntimeError(f'Invalid distribution type: [{self.type}]')
