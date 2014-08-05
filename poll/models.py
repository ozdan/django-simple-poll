# -*- coding: utf-8 -*-

import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.manager import Manager
from django.utils.translation import gettext as _

try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User
else:
    User = get_user_model()


class PublishedManager(Manager):
    def get_query_set(self):
        return super(PublishedManager, self).get_query_set().filter(status=1)


class Poll(models.Model):
    STATUS_CHOICES = (
        (0, _('draft')),
        (1, _('published')),
        (2, _('archival')),
    )
    title = models.CharField(max_length=250, verbose_name=_('question'))
    date = models.DateField(verbose_name=_('date'), default=datetime.date.today)
    publication_date = models.DateTimeField(verbose_name=_('Publication date'), default=datetime.date.today)
    status = models.IntegerField(verbose_name=_('Status'), choices=STATUS_CHOICES, default=0)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ['-date']
        verbose_name = _('poll')
        verbose_name_plural = _('polls')

    def __unicode__(self):
        return self.title

    def get_vote_count(self):
        return Vote.objects.filter(poll=self).count()
    vote_count = property(fget=get_vote_count)

    def get_cookie_name(self):
        return str('poll_%s' % (self.pk))

    def save(self, *args, **kwargs):
        status_changed = False
        if not self.pk: # new object
            status_changed = True
        else:
            orig_obj = Poll.objects.get(pk=self.pk)
            if orig_obj.status != self.status:
                status_changed = True
        if status_changed and self.status == 1:
            self.publication_date = datetime.date.today()
        super(Poll, self).save(*args, **kwargs)


class Item(models.Model):
    poll = models.ForeignKey(Poll)
    value = models.CharField(max_length=250, verbose_name=_('value'))
    pos = models.SmallIntegerField(default='0', verbose_name=_('position'))

    class Meta:
        verbose_name = _('answer')
        verbose_name_plural = _('answers')
        ordering = ['pos']

    def __unicode__(self):
        return u'%s' % (self.value,)

    def get_vote_count(self):
        return Vote.objects.filter(item=self).count()
    vote_count = property(fget=get_vote_count)


class Vote(models.Model):
    poll = models.ForeignKey(Poll, verbose_name=_('poll'))
    item = models.ForeignKey(Item, verbose_name=_('voted item'))
    ip = models.IPAddressField(verbose_name=_('user\'s IP'))
    user = models.ForeignKey(User, blank=True, null=True,
                             verbose_name=_('user'), related_name='uservote')
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('vote')
        verbose_name_plural = _('votes')

    def __unicode__(self):
        if isinstance(self.user, User):
            username_field = getattr(User, 'USERNAME_FIELD', 'username')
            return getattr(User, username_field, '')
        return self.ip
