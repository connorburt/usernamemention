#!/usr/bin/env python

__author__ = 'Connor Burt'

"""

The usernamemention bot aims to provide username mentions for users that
appear in text or linked-based submissions.

"""

import re

import praw

from accountinfo import USERNAME, PASSWORD, CLIENT_ID, CLIENT_SECRET

# Template for username mentions in text-based submissions.
TEXT_TEMPLATE = """
=
##### [{submission_title}]({submission_url})

^^submitted ^^by ^^[{submission_author}]\
(https://www.reddit.com/user/{submission_author})

{submission_content}

=

---
**[^^comments]({comments})**
**[^^give ^^gold]({give_gold})**
"""

# Template for username mentions in link-based submissions.
LINK_TEMPLATE = """
=
##### [{submission_title}]({submission_url})

^^submitted ^^by ^^[{submission_author}]\
(https://www.reddit.com/user/{submission_author})

=

---
**[^^comments]({comments})**
**[^^give ^^gold]({give_gold})**
"""


def main():

    reddit = reddit_object()
    subreddit = reddit.subreddit('all')

    for submission in subreddit.stream.submissions():
        submission_type = submission_type_check(submission)

        if possible_username(submission, submission_type):
            username_list = cleanup(submission, submission_type)

            if len(username_list) > 0:
                send_messages(reddit, submission, username_list,
                              submission_type)
                print ('Message sent!')


# Instantiates the Reddit object.
def reddit_object():

    user_agent = ('u/usernamemention is a Reddit bot that aims to make users',
                  'more aware when they\'re being mentioned in text or',
                  'link-based submissions. (Made by u/connorburt.)')
    reddit = praw.Reddit(user_agent=user_agent,
                         client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                         username=USERNAME, password=PASSWORD)

    return reddit


# Inspects whether submission type is link or text-based.
def submission_type_check(submission):

    if submission.is_self:
        return 'text'

    return 'link'


# Checks whether the submission in question contains a username.
def possible_username(submission, submission_type):

    normalized_title = submission.title.lower()

    if submission_type == 'text':
        normalized_content = submission.selftext.lower()

        if 'u/' in normalized_title or 'u/' in normalized_content:
            return True

    if 'u/' in normalized_title:
        return True


# Compiles all usernames into a nice readable list.
def cleanup(submission, submission_type):

    normalized_title = submission.title.lower()
    submission_author = str(submission.author).lower()
    word_list = []
    username_list = []

    if submission_type == 'text':
        normalized_content = submission.selftext.lower()
        word_list = ('{} {}').format(normalized_title,
                                     normalized_content).split()

    for word in word_list:

        if word.startswith('u/') or word.startswith('/u/'):
            username = re.search(r'(?<=u/)(\w|-)+', word).group(0)

            if (username not in username_list and username != 'usernamemention'
               and username != submission_author):
                username_list.append(username)

    return username_list


# Sends messages to all users included in the username list.
def send_messages(reddit, submission, username_list, submission_type):

    subject = 'username mention'
    give_gold = '{}{}'.format(
        'https://www.reddit.com/gold?goldtype=gift&months=1&thing=',
        submission.fullname)

    if submission_type == 'text':
        message = TEXT_TEMPLATE.format(submission_title=submission.title,
                                       submission_author=submission.author,
                                       submission_url=submission.permalink,
                                       submission_content=adjust_content(
                                           submission.selftext),
                                       comments=submission.shortlink,
                                       give_gold=give_gold)
    else:
        message = LINK_TEMPLATE.format(submission_title=submission.title,
                                       submission_author=submission.author,
                                       submission_url=submission.permalink,
                                       submission_content='',
                                       comments=submission.shortlink,
                                       give_gold=give_gold)

    for user in username_list:
        reddit.redditor(user).message(subject, message)


def adjust_content(submission_content):

    submission_content = re.sub(r'^|\n', '\n> ', submission_content)

    return submission_content


if __name__ == "__main__":
    main()
