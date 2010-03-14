from google.appengine.ext.deferred import deferred
from google.appengine.ext.webapp.util import run_wsgi_app


def main():
  run_wsgi_app(deferred.application)


if __name__ == "__main__":
  main()
