# Introduction

First off, thank you for considering contributing to _elf_diff_. It's people like you that make _elf_diff_ a great tool.

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

_elf_diff_ is an open source project and we love to receive contributions from our community — you! There are many ways to contribute, from improving the documentation, submitting bug reports and feature requests or writing code which can be incorporated into _elf_diff_ itself.

# Ground Rules

Responsibilities

* Ensure cross-platform compatibility for every change that's accepted. Windows, Linux and Mac.
* Ensure that code that goes into core meets all requirements in _elf_diff_'s [PR checklist](PR_CHECKLIST.md)
* Create issues for any major changes and enhancements that you wish to make. Discuss things transparently and get community feedback.
* Keep feature versions as small as possible, preferably one new feature per version.
* Be welcoming to newcomers and encourage diverse new contributors from all backgrounds. See the [Python Community Code of Conduct](https://www.python.org/psf/codeofconduct/).

# Your First Contribution

As a newcomer on a project, it’s easy to experience frustration. Here’s some advice to make your work on _elf_diff_ more useful and rewarding.

* Pick a subject area that you care about, that you are familiar with, or that you want to learn about

* You don’t already have to be an expert on the area you want to work on; you become an expert through your ongoing contributions to the code.

* Analyze tickets’ context and history

* Github isn’t an absolute; the context is just as important as the words. When reading Github, you need to take into account who says things, and when they were said. Support for an idea two years ago doesn’t necessarily mean that the idea will still have support. You also need to pay attention to who hasn’t spoken – for example, if an experienced contributor hasn’t been recently involved in a discussion, then a ticket may not have the support required to get into _elf_diff_.

* Start small

* It’s easier to get feedback on a little issue than on a big one. See the easy pickings.

* If you’re going to engage in a big task, make sure that your idea has support first

* This means getting someone else to confirm that a bug is real before you fix the issue, and ensuring that there’s consensus on a proposed feature before you go implementing it.

* Be bold! Leave feedback!

* Sometimes it can be scary to put your opinion out to the world and say “this ticket is correct” or “this patch needs work”, but it’s the only way the project moves forward. The contributions of the _elf_diff_ community ultimately have a much greater impact than that of any one person. We can’t do it without you!

* Err on the side of caution when marking things Ready For Check-in

* If you’re really not certain if a ticket is ready, don’t mark it as such. Leave a comment instead, letting others know your thoughts. If you’re mostly certain, but not completely certain, you might also try asking on IRC to see if someone else can confirm your suspicions.

* Wait for feedback, and respond to feedback that you receive

* Focus on one or two tickets, see them through from start to finish, and repeat. The shotgun approach of taking on lots of tickets and letting some fall by the wayside ends up doing more harm than good.

* Be rigorous

* When we say “PEP 8, and must have docs and tests”, we mean it. If a patch doesn’t have docs and tests, there had better be a good reason. Arguments like “I couldn’t find any existing tests of this feature” don’t carry much weight–while it may be true, that means you have the extra-important job of writing the very first tests for that feature, not that you get a pass from writing tests altogether.

* Be patient

* It’s not always easy for your ticket or your patch to be reviewed quickly. This isn’t personal. There are sometimes a lot of tickets and pull requests to get through.

* Keeping your patch up to date is important. Review the ticket on Github to ensure that the Needs tests, Needs documentation, and Patch needs improvement flags are unchecked once you’ve addressed all review comments.

Working on your first Pull Request? You can learn how from this *free* series, [How to Contribute to an Open Source Project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github).

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first :smile_cat:

# Getting started

For something that is bigger than a one or two line fix:

1. Create your own fork of the code on Github
2. Do the changes in your fork
3. If you like the change and think the project could use it:
    * Be sure to read the [PR checklist](PR_CHECKLIST.md)
    * Submit a pull request from your fork to _elf_diff_'s repo on Github.
    * Check the Github workflows on your pull request and fix any errors if there are any
      until Github reports the pull request as ready to be merged.
      
If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.

Even small contributions are very welcome.

* Spelling / grammar fixes
* Typo correction, white space and formatting changes
* Comment clean up

If _elf_diff_'s CI Github workflows are reporting error's that you do not understand or cannot fix
by yourself, don't worry there will certainly be experienced developers happy to help you.
Don't hesitate to post related questions in the _Conversation_ section of your Github PR.

# How to report a bug

If you find a security vulnerability, do NOT open an issue. Email shinynoseglasses@gmail.com instead.

When filing an issue on Github, make sure to answer these five questions:

1. What version of Python are you using (`python --version`)?
2. What operating system and processor architecture are you using?
3. What did you do?
4. What did you expect to see?
5. What did you see instead?

# How to suggest a feature or enhancement

If you find yourself wishing for a feature that doesn't exist in _elf_diff_, you are probably not alone. There are bound to be others out there with similar needs. Many of the features that _elf_diff_ has today have been added because our users saw the need. Open an issue on our issues list on GitHub which describes the feature you would like to see, why you need it, and how it should work.

# Coding style

_elf_diff_ uses [Python black](https://pypi.org/project/black/) for its formatting. Any submissions must be formatted with black prior to being submitted as PR. Any code that does not meet this requirement will automatically be rejected by _elf_diff_'s Github workflows that are triggered as part of PR's CI tests. 

# Commit message conventions

Here's a great template of a good commit message originally written by [Tim pope](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html):

> Capitalized, short (50 chars or less) summary
>
> More detailed explanatory text, if necessary.  Wrap it to about 72
> characters or so.  In some contexts, the first line is treated as the
> subject of an email and the rest of the text as the body.  The blank
> line separating the summary from the body is critical (unless you omit
> the body entirely); tools like rebase can get confused if you run the
> two together.
>
> Write your commit message in the imperative: "Fix bug" and not "Fixed bug"
> or "Fixes bug."  This convention matches up with commit messages generated
> by commands like git merge and git revert.
>
> Further paragraphs come after blank lines.
>
> - Bullet points are okay, too
>
> - Typically a hyphen or asterisk is used for the bullet, followed by a
>   single space, with blank lines in between, but conventions vary here
>
> - Use a hanging indent
>
> If you use an issue tracker, add a reference(s) to them at the bottom,
> like so:
>
> Resolves: #123

Please add one of the following prefix to the first line of your commit message
to specify the type of change you are commiting:

* feat: A new feature
* fix: A bug fix
* docs: Documentation only changes
* style: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
* refactor: A code change that neither fixes a bug nor adds a feature
* perf: A code change that improves performance
* test: Adding missing tests
* chore: Changes to the auxiliary tools such as release scripts
* build: Changes to the dependencies, devDependencies, or build tooling
* ci: Changes to our Continuous Integration configuration

If you introduce a breaking change, e.g. to an interface like _elf_diff_'s CLI, please 
add the words `BREAKING CHANGE:` followed by an explanation why the breaking
change is necessary at the end of your commit message.

Example:
```txt
docs(contributing): Add a CONTRIBUTING.md file

This change adds a CONTRIBUTING.md file to the project's repo root.
Its purpose is to inform developers about how to contribute to the
elf_diff project to make _elf_diff_ an even better tool.
```

# Acknowledgments

This CONTRIBUTING file was greatly inspired by the following projects' 
CONTRIBUTING files.

* https://github.com/nayafia/contributing-template
* [Active Admin](https://github.com/activeadmin/activeadmin/blob/master/CONTRIBUTING.md)
* [Hoodie](https://github.com/hoodiehq/hoodie/blob/master/CONTRIBUTING.md)
* [Elasticsearch](https://github.com/elastic/elasticsearch/blob/master/CONTRIBUTING.md)
* [cookiecutter](https://github.com/audreyr/cookiecutter/blob/master/CONTRIBUTING.rst)
* [Django](https://docs.djangoproject.com/en/dev/internals/contributing/new-contributors/#first-steps)
* [React](https://github.com/facebook/react/blob/master/CONTRIBUTING.md#pull-requests)
* [Chef](https://github.com/chef/chef/blob/master/CONTRIBUTING.md#chef-obvious-fix-policy)
* [Go](https://github.com/golang/go/blob/master/CONTRIBUTING.md#filing-issues)
* [Material](https://github.com/angular/material/blob/master/.github/CONTRIBUTING.md#commit)
