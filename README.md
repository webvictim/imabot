imabot
========

A set of Willie modules that perform various useful tasks.

imgurbot.py
-----------

Loads top imgur results from a given subreddit and picks one at random.

```
< webvictim> imgurbot: cats
< imabot> [cats] http://i.imgur.com/2H0pVVT.jpg - "My cat decided he wanted to try on my flip flops."
< webvictim> aww yiss
```

reminder.py
-----------

Remembers reminders for users and plays them back when they next speak.

```
< webvictim> !remind muzak ohai
< imabot> webvictim: Reminder remembered.
< Muzak> wut
< imabot> muzak, webvictim asked me to remind you: ohai
< Muzak> ._.
```

kickvote.py
-----------

Allows people to vote democratically to have a user banned for a while.

```
< jcrza> !votekick testvictim
< imabot> jcrza: Vote for testvictim registered.
< webvictim> !votekick testvictim
< imabot> webvictim: Vote for testvictim registered.
< testvictim> !votekick testvictim
< imabot> testvictim: Voting for yourself?! If you insist... vote registered.
< imabot> testvictim, you are the weakest link. Goodbye!
- NickServ has kicked testvictim (You were democratically kickvoted by jcrza, testvictim and webvictim! (imabot))
- Mode #channel [+b *!*@testvictim.network.lol] by NickServ
```
