# This snippet is in public domain.
# However, please retain this link in your sources:
# http://flask.pocoo.org/snippets/120/
# Danya Alexeyevsky

from flask import session, redirect, current_app, request, url_for
import functools


class back(object):
    """To be used in views.

    Use `anchor` decorator to mark a view as a possible point of return.

    `url()` is the last saved url.

    Use `redirect` to return to the last return point visited.
    """
    cfg = current_app.config.get
    cookie = cfg('REDIRECT_BACK_COOKIE', 'back')
    default_view = cfg('REDIRECT_BACK_DEFAULT', 'index')

    @staticmethod
    def anchor(func, request_url=None, cookie=cookie):
        @functools.wraps(func)
        def result(*args, **kwargs):
            session[cookie] = request_url if request_url else request.url
            return func(*args, **kwargs)
        return result

    @staticmethod
    def url(default=default_view, cookie=cookie):
        return session.get(cookie, '/')

    @staticmethod
    def redirect(default=default_view, cookie=cookie):
        return redirect(back.url(default, cookie))

    @staticmethod
    def set_back_url(value, cookie=cookie):
        session[cookie] =  value

back = back()
