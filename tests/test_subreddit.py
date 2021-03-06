"""Tests for Subreddit class."""

from __future__ import print_function, unicode_literals
from praw import errors
from praw.objects import Subreddit
from six import text_type
from .helper import PRAWTest, betamax


class SubredditTest(PRAWTest):
    def betamax_init(self):
        self.r.login(self.un, self.un_pswd, disable_warning=True)
        self.subreddit = self.r.get_subreddit(self.sr)

    @betamax
    def test_attribute_error(self):
        self.assertRaises(AttributeError, getattr, self.subreddit, 'foo')

    @betamax
    def test_display_name_lazy_update(self):
        augmented_name = self.sr.upper()
        subreddit = self.r.get_subreddit(augmented_name)
        self.assertEqual(augmented_name, text_type(subreddit))
        self.assertNotEqual(augmented_name, subreddit.display_name)
        self.assertEqual(self.sr, subreddit.display_name)
        self.assertEqual(subreddit.display_name, text_type(subreddit))

    @betamax
    def test_display_name_refresh(self):
        augmented_name = self.sr.upper()
        subreddit = self.r.get_subreddit(augmented_name)
        self.assertEqual(augmented_name, text_type(subreddit))
        subreddit.refresh()
        self.assertEqual(self.sr, subreddit.display_name)
        self.assertEqual(subreddit.display_name, text_type(subreddit))

    @betamax
    def test_get_contributors_private(self):
        self.r.login(self.other_non_mod_name, self.other_non_mod_pswd,
                     disable_warning=True)
        private_sub = self.r.get_subreddit(self.priv_sr)
        self.assertEqual('private', private_sub.subreddit_type)
        self.assertTrue(list(private_sub.get_contributors()))

    @betamax
    def test_get_contributors_public(self):
        self.assertEqual('public', self.subreddit.subreddit_type)
        self.assertTrue(list(self.subreddit.get_contributors()))

    @betamax
    def test_get_contributors_public_exception(self):
        self.r.login(self.other_non_mod_name, self.other_non_mod_pswd,
                     disable_warning=True)
        self.assertRaises(errors.ModeratorRequired,
                          self.subreddit.get_contributors)

    @betamax
    def test_get_my_contributions(self):
        predicate = lambda subreddit: text_type(subreddit) == self.sr
        self.first(self.r.get_my_contributions(), predicate)

    @betamax
    def test_get_my_moderation(self):
        predicate = lambda subreddit: text_type(subreddit) == self.sr
        self.first(self.r.get_my_moderation(), predicate)

    @betamax
    def test_get_my_subreddits(self):
        for subreddit in self.r.get_my_subreddits():
            self.assertTrue(text_type(subreddit) in subreddit._info_url)

    @betamax
    def test_subreddit_search(self):
        self.assertTrue(list(self.subreddit.search('test')))

    @betamax
    def test_get_subreddit_recommendations(self):
        result = self.r.get_subreddit_recommendations(['python', 'redditdev'])
        self.assertTrue(result)
        self.assertTrue(all(isinstance(x, Subreddit) for x in result))

    @betamax
    def test_subscribe_and_unsubscribe(self):
        self.subreddit.subscribe()

        self.delay_for_listing_update()
        self.assertTrue(self.subreddit in self.r.get_my_subreddits())
        self.subreddit.unsubscribe()

        self.delay_for_listing_update()
        self.assertFalse(self.subreddit in
                         self.r.get_my_subreddits(params={'u': 1}))


class ModeratorSubredditTest(PRAWTest):
    def betamax_init(self):
        self.r.login(self.un, self.un_pswd, disable_warning=True)
        self.subreddit = self.r.get_subreddit(self.sr)

    @betamax
    def test_get_mod_log(self):
        self.assertTrue(list(self.subreddit.get_mod_log()))

    @betamax
    def test_get_mod_log_with_mod_by_name(self):
        other = self.r.get_redditor(self.other_user_name)
        actions = list(self.subreddit.get_mod_log(mod=other.name))
        self.assertTrue(actions)
        self.assertTrue(all(x.mod.lower() == other.name.lower()
                            for x in actions))

    @betamax
    def test_get_mod_log_with_mod_by_redditor_object(self):
        other = self.r.get_redditor(self.other_user_name)
        actions = list(self.subreddit.get_mod_log(mod=other))
        self.assertTrue(actions)
        self.assertTrue(all(x.mod.lower() == other.name.lower()
                            for x in actions))

    @betamax
    def test_get_mod_log_with_action_filter(self):
        actions = list(self.subreddit.get_mod_log(action='removelink'))
        self.assertTrue(actions)
        self.assertTrue(all(x.action == 'removelink' for x in actions))

    @betamax
    def test_get_mod_queue(self):
        self.assertTrue(list(self.r.get_subreddit('mod').get_mod_queue()))

    @betamax
    def test_get_mod_queue_with_default_subreddit(self):
        self.assertTrue(list(self.r.get_mod_queue()))

    @betamax
    def test_get_mod_queue_multi(self):
        multi = '{0}+{1}'.format(self.sr, self.priv_sr)
        self.assertTrue(list(self.r.get_subreddit(multi).get_mod_queue()))

    @betamax
    def test_get_unmoderated(self):
        self.assertTrue(list(self.subreddit.get_unmoderated()))

    @betamax
    def test_mod_mail_send(self):
        subject = 'Unique message: AAAA'
        self.r.get_subreddit(self.sr).send_message(subject, 'Content')
        self.first(self.r.get_mod_mail(), lambda msg: msg.subject == subject)

    @betamax
    def test_set_settings(self):
        # The only required argument is title. All others will be set
        # to their defaults.
        title = 'Reddit API Test {0}'.format(self.r.modhash)
        self.subreddit.set_settings(title)
        settings = self.subreddit.get_settings()
        self.assertEqual(title, settings['title'])
        for setting in ['description', 'public_description']:
            self.assertEqual('', settings[setting])

    @betamax
    def test_set_stylesheet(self):
        self.assertRaises(errors.BadCSS, self.subreddit.set_stylesheet,
                          'INVALID CSS')

        stylesheet = ('div.titlebox span.number:after {{\ncontent: " {0}"\n}}'
                      .format(self.r.modhash))
        self.subreddit.set_stylesheet(stylesheet)
        self.assertEqual(stylesheet,
                         self.subreddit.get_stylesheet()['stylesheet'])

        self.subreddit.set_stylesheet('')
        self.assertEqual(
            '', self.subreddit.get_stylesheet(uniq=1)['stylesheet'])

    @betamax
    def test_update_settings__descriptions(self):
        self.maxDiff = None
        settings = self.subreddit.get_settings()
        settings['description'] = 'Description {0}'.format(self.r.modhash)
        settings['public_description'] = ('Public Description {0}'
                                          .format(self.r.modhash))
        self.subreddit.update_settings(
            description=settings['description'],
            public_description=settings['public_description'])
        self.assertEqual(settings, self.subreddit.get_settings(uniq=1))
